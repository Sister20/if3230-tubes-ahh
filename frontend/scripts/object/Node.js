export class Node {
  id = null;
  name = null;
  port = null;
  status = null;
  focus = null;
  log = [];

  constructor(id, name, port, status = "inactive") {
    this.id = id;
    this.name = name;
    this.port = port;
    this.status = status;
    this.focus = false;
    this.log = [];
  }
}
