class Point {
  public:
    int x;
    int y;
    Point(int newX, int newY);
    Point();
    Point operator+(const Point& other);
    Point operator-(const Point& other);
    bool operator==(const Point& other);
    bool operator!=(const Point& other);
};

Point::Point(int newX, int newY) {
  x = newX;
  y = newY;
}

Point::Point() {
  x = 0;
  y = 0;
}

Point Point::operator+(const Point& other){
  return Point(x+other.x, y+other.y);
}
Point Point::operator-(const Point& other){
  return Point(x-other.x, y-other.y);
}
bool Point::operator==(const Point& other){
  return x==other.x && y==other.y;
}
bool Point::operator!=(const Point& other){
  return x!=other.x || y!=other.y;
}
