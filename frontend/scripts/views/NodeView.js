import { NodeController } from "../controller/NodeController.js";
import { NodeModels } from "../models/NodeModels.js";

export class NodeView {
  static _dom = null;

  static init(dom) {
    NodeView._dom = dom;
  }

  static _renderItem(node) {
    const newNode = document.createElement("li");
    newNode.classList.add("component");
    if (node.focus) newNode.classList.add("focus");
    else if (node.status === "inactive") newNode.classList.add("inactive");
    newNode.setAttribute("data-id", node.id);
    newNode.setAttribute("data-port", node.port);
    newNode.innerHTML = `<p>${node.name}</p>`;

    newNode.addEventListener("click", (event) => {
      const id = parseInt(event.currentTarget.getAttribute("data-id"));
      NodeController.setFocus(id);
    });

    NodeView._dom.appendChild(newNode);
  }

  static render() {
    NodeView._dom.innerHTML = "";

    NodeModels.nodes.forEach((node) => {
      NodeView._renderItem(node);
    });
  }
}
