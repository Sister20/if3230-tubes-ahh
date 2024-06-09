export class NodeModels {
  static _nodes = [];
  static _focusedNodeId = null;

  static init() {
    NodeModels._nodes = [
      {
        id: 1,
        name: "Node 1",
        status: "active",
        port: 3001,
        focus: true,
      },
      {
        id: 2,
        name: "Node 2",
        status: "active",
        port: 3002,
        focus: false,
      },
      {
        id: 3,
        name: "Node 3",
        status: "active",
        port: 3003,
        focus: false,
      },
      {
        id: 4,
        name: "Node 4",
        status: "inactive",
        port: 3004,
        focus: false,
      },
      {
        id: 5,
        name: "Node 5",
        status: "inactive",
        port: 3005,
        focus: false,
      },
      {
        id: 6,
        name: "Node 6",
        status: "inactive",
        port: 3006,
        focus: false,
      },
      {
        id: 7,
        name: "Node 7",
        status: "inactive",
        port: 3007,
        focus: false,
      },
      {
        id: 8,
        name: "Node 8",
        status: "inactive",
        port: 3008,
        focus: false,
      },
      {
        id: 9,
        name: "Node 9",
        status: "inactive",
        port: 3009,
        focus: false,
      },
      {
        id: 10,
        name: "Node 10",
        status: "inactive",
        port: 3010,
        focus: false,
      },
    ];
    NodeModels._focusedNodeId = 1;
  }

  static get nodes() {
    return this._nodes;
  }

  static set focusedNodeId(id) {
    NodeModels._focusedNodeId = id;
  }
}
