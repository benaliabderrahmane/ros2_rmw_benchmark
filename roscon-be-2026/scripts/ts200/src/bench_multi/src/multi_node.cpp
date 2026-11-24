// One process == one ROS node with P publishers and S subscriptions, for the supervised 200-node time series.
//
// Node i publishes /bench/t<i>_<k> for k < P and subscribes, for k < S, to /bench/t<(i - 1 - k) mod N>_<k mod P>:
// S interleaved rings, so with P = S every topic has exactly one publisher and one subscriber. The message, QoS and
// rate are load_node's (ros2_rmw_benchmark): a 256 B std_msgs/String with a CLOCK_MONOTONIC header, reliable,
// KEEP_LAST 10, 20 Hz, every publisher on each tick.
//
// "Up": once every subscription has received at least one message, the node writes its monotonic time (ns) to
// <ready-dir>/ready_<i> (temp file + rename, once). The supervisor (ts200.py) reads it. Runs until SIGINT/SIGTERM.

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

namespace
{
constexpr int TS_DIGITS = 20;
constexpr int SEQ_DIGITS = 20;
constexpr int HEADER_BYTES = TS_DIGITS + SEQ_DIGITS;

int64_t mono_ns()
{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return static_cast<int64_t>(ts.tv_sec) * 1000000000LL + ts.tv_nsec;
}

const char * arg(int argc, char ** argv, const char * key, const char * def)
{
  for (int i = 1; i < argc - 1; ++i) {
    if (std::strcmp(argv[i], key) == 0) {return argv[i + 1];}
  }
  return def;
}
}  // namespace

int main(int argc, char ** argv)
{
  const int id = std::atoi(arg(argc, argv, "--id", "0"));
  const int total = std::max(1, std::atoi(arg(argc, argv, "--total", "1")));
  const int pubs = std::max(1, std::atoi(arg(argc, argv, "--pubs", "5")));
  const int subs = std::max(1, std::atoi(arg(argc, argv, "--subs", "5")));
  const double rate = std::atof(arg(argc, argv, "--rate", "20"));
  const int size = std::max(HEADER_BYTES, std::atoi(arg(argc, argv, "--size", "256")));
  const std::string ready_dir = arg(argc, argv, "--ready-dir", "");

  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("bench_node_" + std::to_string(id));
  rclcpp::QoS qos(rclcpp::KeepLast(10));
  qos.reliable();

  std::vector<rclcpp::Publisher<std_msgs::msg::String>::SharedPtr> pub;
  for (int k = 0; k < pubs; ++k) {
    pub.push_back(node->create_publisher<std_msgs::msg::String>(
        "/bench/t" + std::to_string(id) + "_" + std::to_string(k), qos));
  }

  std::vector<bool> got(static_cast<size_t>(subs), false);
  int missing = subs;
  bool written = false;
  std::vector<rclcpp::Subscription<std_msgs::msg::String>::SharedPtr> sub;
  for (int k = 0; k < subs; ++k) {
    const int sender = ((id - 1 - k) % total + total) % total;
    sub.push_back(node->create_subscription<std_msgs::msg::String>(
        "/bench/t" + std::to_string(sender) + "_" + std::to_string(k % pubs), qos,
        [&, k](const std_msgs::msg::String &) {
          if (got[static_cast<size_t>(k)]) {return;}
          got[static_cast<size_t>(k)] = true;
          if (--missing == 0 && !written && !ready_dir.empty()) {
            written = true;
            const std::string path = ready_dir + "/ready_" + std::to_string(id);
            {
              std::ofstream f(path + ".tmp");
              f << mono_ns() << "\n";
            }
            std::rename((path + ".tmp").c_str(), path.c_str());
          }
        }));
  }

  std::string payload(static_cast<size_t>(size), 'x');
  int64_t seq = 0;
  const auto period = std::chrono::duration_cast<std::chrono::nanoseconds>(
    std::chrono::duration<double>(1.0 / (rate > 0 ? rate : 1.0)));
  auto timer = node->create_wall_timer(period, [&]() {
      for (auto & p : pub) {
        std_msgs::msg::String m;
        m.data = payload;
        char hdr[HEADER_BYTES + 1];
        std::snprintf(hdr, sizeof(hdr), "%0*lld%0*lld", TS_DIGITS, static_cast<long long>(mono_ns()),
          SEQ_DIGITS, static_cast<long long>(seq));
        std::memcpy(&m.data[0], hdr, HEADER_BYTES);
        p->publish(m);
      }
      ++seq;
    });

  rclcpp::executors::SingleThreadedExecutor exec;
  exec.add_node(node);
  exec.spin();  // returns on SIGINT/SIGTERM (rclcpp's signal handler shuts the context down)
  rclcpp::shutdown();
  return 0;
}
