import { NodeModels } from "../models/NodeModels.js";
import { LogView } from "../views/LogView.js";
import { NodeView } from "../views/NodeView.js";

export class NodeController {
  static setup() {
    NodeModels.init();
    NodeView.init(document.querySelector("#node-list"));
    LogView.init(document.querySelector("#log-msg"));
    NodeController.setFocus(1);
  }

  static render() {
    NodeView.render();
    LogView.render();
  }

  static setFocus(id) {
    let focusNode = null;
    NodeModels.nodes.forEach((node) => {
      if (node.id === id) {
        focusNode = node;
        node.focus = true;
      } else {
        node.focus = false;
      }
    });

    NodeModels._focus = focusNode;

    NodeView.render();
    LogView.render();
  }

  static updateLog() {
    NodeModels.nodes.forEach((node) => {
      node.updateLog();
    });
  }
}
