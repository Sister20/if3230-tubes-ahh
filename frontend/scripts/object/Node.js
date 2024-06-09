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

  updateLog() {
    try {
      const websocket = new WebSocket(`ws://localhost:8000/log/${this.port}`);
      this.status = "active";
      const node = this;
      websocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (data.log) node.log.push(data.log);
        else if (data.error) node.status = "inactive";
      };
    } catch (error) {
      this.status = "inactive";
    }
  }
}
