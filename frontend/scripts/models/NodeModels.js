import { NodeController } from "../controller/NodeController.js";
import { Node } from "../object/Node.js";

export class NodeModels {
  static _nodes = [];
  static _focus = null;

  static init() {
    NodeModels._nodes = [
      new Node(1, "Node 1", 3001),
      new Node(2, "Node 2", 3002),
      new Node(3, "Node 3", 3003),
      new Node(4, "Node 4", 3004),
      new Node(5, "Node 5", 3005),
      new Node(6, "Node 6", 3006),
      new Node(7, "Node 7", 3007),
      new Node(8, "Node 8", 3008),
      new Node(9, "Node 9", 3009),
      new Node(10, "Node 10", 3010),
    ];
  }

  static get nodes() {
    return NodeModels._nodes;
  }

  static get focus() {
    return NodeModels._focus;
  }

  static set focus(node) {
    NodeModels._focus = node;
  }
}
