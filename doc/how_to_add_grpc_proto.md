How to add a grpc proto
=======================

1. Every grpc service should correspond to exactly 1 of the following:
    1. Nebula model
    2. Nebula service
2. For every user facing function in the class, add one rpc
3. Follow the [protobuf google style guide](https://protobuf.dev/programming-guides/style/)