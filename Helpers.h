class Point {
  public:
    Point(int newX, int newY);
    Point();

    Point operator+(const Point& other);
    Point operator-(const Point& other);
    bool operator==(const Point& other);
    bool operator!=(const Point& other);

    int x;
    int y;
    Point sign();
};

Point::Point(int newX, int newY) {
  x = newX;
  y = newY;
}

Point::Point() {
  x = 0;
  y = 0;
}

Point Point::operator+(const Point& other) {
  return Point(x + other.x, y + other.y);
}
Point Point::operator-(const Point& other) {
  return Point(x - other.x, y - other.y);
}
bool Point::operator==(const Point& other) {
  return x == other.x && y == other.y;
}
bool Point::operator!=(const Point& other) {
  return x != other.x || y != other.y;
}

Point Point::sign() {
  int xSign = 0;
  int ySign = 0;

  if (x > 0) {
    xSign = 1;
  }
  else if (x < 0) {
    xSign = -1;
  }

  if (y > 0) {
    ySign = 1;
  }
  else if (y < 0) {
    ySign = -1;
  }
  
  return Point(xSign, ySign);
}

