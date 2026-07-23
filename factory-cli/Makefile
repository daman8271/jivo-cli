.PHONY: build test lint install clean

build:
	go build -o bin/jivo-factory-pp-cli ./cmd/jivo-factory-pp-cli

test:
	go test ./...

lint:
	golangci-lint run

install:
	go install ./cmd/jivo-factory-pp-cli

clean:
	rm -rf bin/

build-mcp:
	go build -o bin/jivo-factory-pp-mcp ./cmd/jivo-factory-pp-mcp

install-mcp:
	go install ./cmd/jivo-factory-pp-mcp

build-all: build build-mcp
