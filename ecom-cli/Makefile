.PHONY: build test lint install clean

build:
	go build -o bin/jivo-ecom-pp-cli ./cmd/jivo-ecom-pp-cli

test:
	go test ./...

lint:
	golangci-lint run

install:
	go install ./cmd/jivo-ecom-pp-cli

clean:
	rm -rf bin/

build-mcp:
	go build -o bin/jivo-ecom-pp-mcp ./cmd/jivo-ecom-pp-mcp

install-mcp:
	go install ./cmd/jivo-ecom-pp-mcp

build-all: build build-mcp
