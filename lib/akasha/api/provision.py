"""Boot provisioning hooks — `fn(kernel)`, run by the heart as admin in ascending `order` (the
package manifests' `depends_on` fixes the order across packages; `order` orders within one).

Provisioning writes what the declarations say (benches, societies, workflows, workloads) and is
idempotent; it is the ONE place application code obtains an admin session (§A21 rule 6). In this
seed the workbench's provisioning still runs from its schedule body; the registry is the seam it
moves to, so the heart never names a provisioner.
"""
from typing import Callable, Dict, List, Tuple


class ProvisionRegistry:
    def __init__(self):
        self._hooks: Dict[str, Tuple[Callable, int, str]] = {}

    def register(self, name: str, fn: Callable, order: int = 100, source: str = "") -> None:
        if name in self._hooks:
            raise ValueError(f"provisioner {name!r} defined twice: {self._hooks[name][2]} and {source}")
        self._hooks[name] = (fn, int(order), source)

    def ordered(self) -> List[Tuple[str, Callable]]:
        rows = sorted(self._hooks.items(), key=lambda kv: (kv[1][1], kv[0]))
        return [(name, fn) for name, (fn, _o, _s) in rows]

    def run(self, kernel) -> None:
        for name, fn in self.ordered():
            fn(kernel)

    def names(self) -> List[str]:
        return sorted(self._hooks)
