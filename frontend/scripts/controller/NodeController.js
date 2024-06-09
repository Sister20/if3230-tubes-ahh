import { NodeModels } from "../models/NodeModels.js";
import { NodeView } from "../views/NodeView.js";

export class NodeController {
  static setup() {
    NodeModels.init();
    NodeView.init(document.querySelector("#node-list"));
  }

  static render() {
    NodeView.render();
  }

  static setFocus(id) {
    NodeModels.focusedNodeId = id;

    NodeModels.nodes.forEach((node) => {
      if (node.id === id) node.focus = true;
      else node.focus = false;
    });

    NodeView.render();
  }
}
