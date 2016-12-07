CFLAGS=-c -Wall -std=c++11 -g -Werror
CFLAGS += -I/usr/local/include
LDFLAGS = -lzmq
SOURCES=main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=cpdk-test

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS) 
	$(CXX) $(OBJECTS) -o $@ $(LDFLAGS)

.cpp.o:
	$(CXX) $(CFLAGS) $< -o $@

clean:
	rm -f *.o $(EXECUTABLE)

