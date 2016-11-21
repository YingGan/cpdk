CC=g++
CFLAGS=-c -Wall -std=c++11 -g
CFLAGS += -I/usr/local/include -I./msgpack/include -I./zeromq
LDFLAGS = -lzmq
SOURCES=main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=cpdk-test

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS) 
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

.cpp.o:
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f *.o $(EXECUTABLE)
