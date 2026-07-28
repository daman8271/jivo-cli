.PHONY: build test lint install clean

build:
	go build -o bin/jivo-pp-cli ./cmd/jivo-pp-cli

test:
	go test ./...

lint:
	golangci-lint run

install:
	go install ./cmd/jivo-pp-cli

clean:
	rm -rf bin/

build-mcp:
	go build -o bin/jivo-pp-mcp ./cmd/jivo-pp-mcp

install-mcp:
	go install ./cmd/jivo-pp-mcp

build-all: build build-mcp
