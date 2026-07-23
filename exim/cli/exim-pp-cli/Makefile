.PHONY: build test lint install clean

build:
	go build -o bin/exim-pp-cli ./cmd/exim-pp-cli

test:
	go test ./...

lint:
	golangci-lint run

install:
	go install ./cmd/exim-pp-cli

clean:
	rm -rf bin/

build-mcp:
	go build -o bin/exim-pp-mcp ./cmd/exim-pp-mcp

install-mcp:
	go install ./cmd/exim-pp-mcp

build-all: build build-mcp
