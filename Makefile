CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Werror -Wpedantic -fstack-protector-strong
.PHONY: all test sanitize proto clean
all: build/libatlas.so
build/libatlas.so: engine/policy.c engine/policy.h
	mkdir -p build
	$(CC) $(CFLAGS) -fPIC -shared engine/policy.c -o $@
test: all
	$(CC) $(CFLAGS) engine/policy.c engine/test_policy.c -o build/test_policy
	./build/test_policy
sanitize:
	mkdir -p build
	$(CC) -std=c11 -g -Wall -Wextra -Werror -fsanitize=address,undefined engine/policy.c engine/test_policy.c -o build/test_sanitize
	./build/test_sanitize
proto:
	python -m grpc_tools.protoc -I proto --python_out=services/policy --grpc_python_out=services/policy proto/policy.proto
clean:
	rm -rf build
