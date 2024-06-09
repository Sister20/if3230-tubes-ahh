import { NodeController } from "./controller/NodeController.js";

NodeController.setup();
NodeController.updateLog();

function render() {
  NodeController.render();

  setTimeout(render, 1000);
}

render();
