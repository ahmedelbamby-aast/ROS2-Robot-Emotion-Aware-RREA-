# Foundation Topic Contract

This document is the source of truth for required ROS topics and message contracts.

## Operational Reality (May 20, 2026)

- This contract is used in both deployment modes:
  - `robot_only`
  - `laptop_offload` (robot feed + laptop inference + robot speaker output)
- Camera source constraints apply at runtime:
  - `vision.source=uvc` expects `/dev/video*`
  - `vision.source=astra` expects ORBBEC ASTRA over `/dev/bus/usb` (non-UVC path)
- For offload mode validation, laptop gateway must be started before robot endpoint.

## Status (May 19, 2026)

- Contract topics below are implemented in the current pipeline.
- Topic presence is not equivalent to full AI quality completion.
- Vision/audio labels can currently come from heuristic logic paths; full model-quality behavior is tracked as Phase 2 open work.

## Required Runtime Topics

| Topic | Message Type | Producer | Consumer |
| --- | --- | --- | --- |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | Robot camera driver or capture node | `camera_emotion_node`, `robot_gateway_node` |
| `/camera/emotion` | `std_msgs/msg/String` | `camera_emotion_node` or laptop inference path | `fusion_node` |
| `/audio/raw` | `std_msgs/msg/UInt8MultiArray` | Robot mic path | `audio_emotion_node`, `stt_node`, `robot_gateway_node` |
| `/audio/emotion` | `std_msgs/msg/String` | `audio_emotion_node` or laptop inference path | `fusion_node` |
| `/speech/text` | `std_msgs/msg/String` | `stt_node` | `sentiment_node`, `response_node`, gateway nodes |
| `/text/sentiment` | `std_msgs/msg/String` | `sentiment_node` | `fusion_node` |
| `/emotion/final` | `std_msgs/msg/String` | `fusion_node` | `response_node`, gateway nodes |
| `/robot/response` | `std_msgs/msg/String` | `response_node` | Gateway node, observers |
| `/robot/say` | `std_msgs/msg/String` | `response_node` | `tts_node`, gateway nodes |

## Optional Status Topics

| Topic | Message Type | Producer |
| --- | --- | --- |
| `/speech/stt_status` | `std_msgs/msg/String` | `stt_node` |
| `/speech/tts_status` | `std_msgs/msg/String` | `tts_node` |

## Contracts

- Emotion labels must be one of: `happy`, `sad`, `angry`, `neutral`.
- Sentiment labels must be one of: `positive`, `negative`, `neutral`.
- Required topics in this file must exist in both `robot_only` and `laptop_offload` flows.

## Contract Verification Checklist

- [x] Topic names and message types documented.
- [x] Producers and consumers assigned.
- [ ] Runtime verification artifacts attached for `robot_only`.
- [ ] Runtime verification artifacts attached for `laptop_offload`.
- [ ] QoS expectations documented for each required topic.
