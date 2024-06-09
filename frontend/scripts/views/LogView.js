import { NodeModels } from "../models/NodeModels.js";

export class LogView {
  static _dom = null;

  static init(dom) {
    LogView._dom = dom;
  }

  static render() {
    LogView._dom.innerHTML = "";

    const focusNode = NodeModels.focus;

    if (focusNode.log.length > 0) {
      LogView._dom.innerHTML = focusNode.log
        .map((msg) => `<p>${msg}</p>`)
        .join("");
    } else {
      LogView._dom.innerHTML =
        "<p style='color: var(--text-500)'>No log found</p>";
    }
  }
}
