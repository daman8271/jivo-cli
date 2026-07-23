.PHONY: build test lint install clean

build:
	go build -o bin/oms-pp-cli ./cmd/oms-pp-cli

test:
	go test ./...

lint:
	golangci-lint run

install:
	go install ./cmd/oms-pp-cli

clean:
	rm -rf bin/

build-mcp:
	go build -o bin/oms-pp-mcp ./cmd/oms-pp-mcp

install-mcp:
	go install ./cmd/oms-pp-mcp

build-all: build build-mcp
