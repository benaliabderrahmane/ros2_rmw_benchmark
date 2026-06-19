// Benchmark load node: one process == one ROS node.
//
// Ring topology: node i publishes on /bench/t<i> and subscribes to
// /bench/t<sender> where sender = (i - 1 + total) % total. Every node both
// publishes and subscribes, so N nodes create N participants and N flows --
// representative load for measuring per-node RAM/CPU, discovery time, and
// cross-node latency at scale.
//
// Two message modes:
//   default     std_msgs/String with a CLOCK_MONOTONIC timestamp in an ASCII
//               header (variable-length; what most ROS topics look like).
//   --fixed     bench_nodes/FixedMsg: a plain fixed-size type that qualifies
//               for DDS zero-copy shared memory (Iceoryx / data-sharing).
//
// CLOCK_MONOTONIC is system-wide on Linux, so cross-process timestamps are
// directly comparable on a single host. On exit each node writes a small JSON
// file the orchestrator aggregates.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "bench_nodes/msg/fixed_msg.hpp"

namespace
{
constexpr int TS_DIGITS = 20;   // monotonic ns, max int64 ~= 9.2e18 -> 19 digits
constexpr int SEQ_DIGITS = 20;
constexpr int HEADER_BYTES = TS_DIGITS + SEQ_DIGITS;

int64_t mono_ns()
{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return static_cast<int64_t>(ts.tv_sec) * 1000000000LL + ts.tv_nsec;
}

struct Args
{
  int id = 0;
  int total = 1;
  double rate = 20.0;
  int size = 256;
  double duration = 15.0;
  double warmup = 3.0;
  bool fixed = false;
  std::string out;
};

const char * arg_value(int argc, char ** argv, const char * key)
{
  for (int i = 1; i < argc - 1; ++i) {
    if (std::strcmp(argv[i], key) == 0) {
      return argv[i + 1];
    }
  }
  return nullptr;
}

bool arg_flag(int argc, char ** argv, const char * key)
{
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], key) == 0) {return true;}
  }
  return false;
}

Args parse_args(int argc, char ** argv)
{
  Args a;
  if (const char * v = arg_value(argc, argv, "--id")) {a.id = std::atoi(v);}
  if (const char * v = arg_value(argc, argv, "--total")) {a.total = std::atoi(v);}
  if (const char * v = arg_value(argc, argv, "--rate")) {a.rate = std::atof(v);}
  if (const char * v = arg_value(argc, argv, "--size")) {a.size = std::atoi(v);}
  if (const char * v = arg_value(argc, argv, "--duration")) {a.duration = std::atof(v);}
  if (const char * v = arg_value(argc, argv, "--warmup")) {a.warmup = std::atof(v);}
  if (const char * v = arg_value(argc, argv, "--out")) {a.out = v;}
  a.fixed = arg_flag(argc, argv, "--fixed");
  if (a.total < 1) {a.total = 1;}
  if (a.size < HEADER_BYTES) {a.size = HEADER_BYTES;}
  return a;
}

// Runs the publish/subscribe ring for one message type. `stamp` writes the
// monotonic send-time + seq into a message; `read_ts` extracts the send-time
// from a received message. The executor blocks (spin), so idle CPU reflects the
// RMW's real wait behaviour, not a poll loop.
template<typename MsgT, typename Stamp, typename Read>
void run(const rclcpp::Node::SharedPtr & node, const Args & args, int sender,
  Stamp stamp, Read read_ts)
{
  rclcpp::QoS qos(rclcpp::KeepLast(10));
  qos.reliable();

  auto pub = node->create_publisher<MsgT>("/bench/t" + std::to_string(args.id), qos);

  int64_t t_first_recv_ns = -1;
  int64_t n_recv = 0;
  std::vector<double> latencies_us;
  latencies_us.reserve(static_cast<size_t>(args.rate * args.duration) + 16);

  const int64_t start_ns = mono_ns();
  const int64_t warmup_ns = start_ns + static_cast<int64_t>(args.warmup * 1e9);
  const int64_t end_ns = start_ns + static_cast<int64_t>(args.duration * 1e9);

  auto on_msg =
    [&](const MsgT & msg) {
      const int64_t recv_ns = mono_ns();
      const int64_t send_ns = read_ts(msg);
      if (send_ns <= 0) {return;}
      if (t_first_recv_ns < 0) {t_first_recv_ns = recv_ns;}
      ++n_recv;
      if (recv_ns >= warmup_ns) {
        latencies_us.push_back(static_cast<double>(recv_ns - send_ns) / 1000.0);
      }
    };
  auto sub = node->create_subscription<MsgT>(
    "/bench/t" + std::to_string(sender), qos, on_msg);

  const int64_t t_ready_ns = mono_ns();

  rclcpp::executors::SingleThreadedExecutor exec;
  exec.add_node(node);

  int64_t seq = 0;
  int64_t n_sent = 0;
  const auto period = std::chrono::duration_cast<std::chrono::nanoseconds>(
    std::chrono::duration<double>(1.0 / (args.rate > 0 ? args.rate : 1.0)));
  auto pub_timer = node->create_wall_timer(period, [&]() {
      MsgT msg;
      stamp(msg, mono_ns(), seq);
      pub->publish(msg);
      ++seq;
      ++n_sent;
    });
  auto stop_timer = node->create_wall_timer(std::chrono::milliseconds(20), [&]() {
      if (!rclcpp::ok() || mono_ns() >= end_ns) {
        exec.cancel();
      }
    });
  exec.spin();

  if (!args.out.empty()) {
    std::ofstream f(args.out);
    f << "{\n";
    f << "  \"idx\": " << args.id << ",\n";
    f << "  \"expected_sender\": " << sender << ",\n";
    f << "  \"t_ready_ns\": " << t_ready_ns << ",\n";
    f << "  \"t_first_recv_ns\": " << t_first_recv_ns << ",\n";
    f << "  \"n_sent\": " << n_sent << ",\n";
    f << "  \"n_recv\": " << n_recv << ",\n";
    f << "  \"latencies_us\": [";
    for (size_t i = 0; i < latencies_us.size(); ++i) {
      if (i) {f << ",";}
      char buf[32];
      std::snprintf(buf, sizeof(buf), "%.2f", latencies_us[i]);
      f << buf;
    }
    f << "]\n}\n";
  }
}
}  // namespace

int main(int argc, char ** argv)
{
  Args args = parse_args(argc, argv);
  rclcpp::init(argc, argv);

  const int sender = (args.id - 1 + args.total) % args.total;
  auto node = rclcpp::Node::make_shared("bench_node_" + std::to_string(args.id));

  if (args.fixed) {
    using Msg = bench_nodes::msg::FixedMsg;
    run<Msg>(
      node, args, sender,
      [](Msg & m, int64_t ts, int64_t s) {m.send_ns = ts; m.seq = s;},
      [](const Msg & m) {return m.send_ns;});
  } else {
    using Msg = std_msgs::msg::String;
    std::string payload(static_cast<size_t>(args.size), 'x');
    run<Msg>(
      node, args, sender,
      [&payload](Msg & m, int64_t ts, int64_t s) {
        m.data = payload;
        char hdr[HEADER_BYTES + 1];
        std::snprintf(
          hdr, sizeof(hdr), "%0*lld%0*lld",
          TS_DIGITS, static_cast<long long>(ts), SEQ_DIGITS, static_cast<long long>(s));
        std::memcpy(&m.data[0], hdr, HEADER_BYTES);
      },
      [](const Msg & m) -> int64_t {
        if (m.data.size() < static_cast<size_t>(TS_DIGITS)) {return -1;}
        return std::strtoll(m.data.substr(0, TS_DIGITS).c_str(), nullptr, 10);
      });
  }

  rclcpp::shutdown();
  return 0;
}
