# Part II · 3. Packages and Scope

[← Enhanced Data Types](02-enhanced-data-types.md) · [Table of contents](../README.md) · [Next: Interfaces and Modports →](04-interfaces-and-modports.md)

## Learning objectives

- Define a `package` to hold shared types, parameters, and functions.
- Import package items explicitly or with a wildcard.
- Understand `$unit` scope and why explicit packages are preferred.
- Use packages to share definitions across modules without copy-paste.

## The problem packages solve

In a Verilog design, a type defined in one module is not visible in another.
Designers work around this by duplicating `typedef`, `parameter`, and `localparam`
declarations in every module that needs them. When the definition changes, every
copy must be updated — a maintenance problem and a source of subtle mismatches.

SystemVerilog packages solve this. A package is a named namespace that holds
type definitions, parameters, constants, and functions. Any module can import
from a package and use its contents without duplication.

## Declaring a package

```systemverilog
package bus_pkg;

    // Shared parameters
    parameter int DATA_WIDTH = 32;
    parameter int ADDR_WIDTH = 16;

    // Shared types
    typedef logic [DATA_WIDTH-1:0] data_t;
    typedef logic [ADDR_WIDTH-1:0] addr_t;

    typedef enum logic [1:0] {
        READ  = 2'b00,
        WRITE = 2'b01,
        BURST = 2'b10,
        IDLE  = 2'b11
    } cmd_t;

    typedef struct packed {
        addr_t  addr;
        data_t  data;
        cmd_t   cmd;
        logic   valid;
    } bus_req_t;

endpackage
```

A package looks like a module in syntax, but it has no ports and instantiates
nothing. It is compiled once and its contents are available by name to any
module that imports it.

Packages may not contain `always` blocks, `initial` blocks, or module
instantiations. They hold declarations only.

## Importing from a package

### Explicit import

An explicit import brings one named item into scope:

```systemverilog
import bus_pkg::DATA_WIDTH;
import bus_pkg::bus_req_t;

module memory_ctrl (
    input  bus_pkg::bus_req_t req,   // qualified name, no import needed
    output logic [DATA_WIDTH-1:0] rdata
);
```

You can also use the package name directly as a qualifier without importing:
`bus_pkg::bus_req_t`. This is the most explicit form and makes the origin clear at
every use site.

### Wildcard import

A wildcard import brings all names from a package into scope, subject to
resolution rules:

```systemverilog
import bus_pkg::*;

module memory_ctrl (
    input  bus_req_t req,
    output data_t    rdata
);
```

Wildcard imports are convenient but can cause name collisions when two packages
define the same identifier. Explicit imports or qualified names are safer in
large designs where multiple packages are in use.

### Import in the port list

You can import inside the module header, before the port list, so the imported
names are available in port declarations:

```systemverilog
module memory_ctrl
    import bus_pkg::*;
(
    input  bus_req_t  req,
    output data_t     rdata,
    input  logic      clk,
    input  logic      rst_n
);
```

This is the idiomatic SystemVerilog style for modules that depend heavily on one
package.

## Packages hold parameters too

Sharing parameters through packages is cleaner than defining them in a top-level
module or passing them through the parameter ports of every module.

```systemverilog
package config_pkg;
    parameter int FIFO_DEPTH    = 16;
    parameter int PIPELINE_STAGES = 4;
    localparam int ADDR_BITS    = $clog2(FIFO_DEPTH);
endpackage
```

Any module that needs `FIFO_DEPTH` imports `config_pkg` and uses the name
directly. A single change to the package propagates everywhere on recompilation.

Note that `localparam` in a package cannot be overridden by a parent — it is a
computed constant. `parameter` in a package can in principle be overridden by a
parameterized package instantiation, but this feature is rarely used in practice.
For shared constants that should never be overridden, `localparam` is safer.

## `$unit` scope

SystemVerilog has a compilation-unit scope, written `$unit`, that is the implicit
global namespace for a compilation unit (roughly, one invocation of the compiler).
Declarations made outside any module or package fall into `$unit` and are visible
to everything compiled in the same unit.

```systemverilog
// In $unit scope (outside any module/package)
typedef logic [7:0] byte_t;   // visible to all modules in this compilation unit
```

`$unit` works but is fragile:

- Its contents depend on file ordering and tool invocation, making the design
  sensitive to compilation order.
- Two compilation units may not share the same `$unit` scope, breaking designs
  that span multiple compilation jobs.
- It provides no namespacing — everything lands in one flat global namespace.

Prefer explicit packages over `$unit`. The discipline of declaring a package and
importing from it makes dependencies visible and the design portable across tools
and compilation strategies.

> **Design intent.** A package expresses that a set of definitions belongs
> together and is shared by design contract. When you see `import bus_pkg::*` at
> the top of a module, you immediately know that module participates in the bus
> protocol defined in that package. The package is the specification; the import
> is the claim.

## Organizing packages in a project

A common pattern is one package per protocol or subsystem:

```text
bus_pkg        — bus types and widths
config_pkg     — top-level parameters and derived constants
alu_pkg        — ALU opcodes and control types
soc_pkg        — SoC-level enumerations
```

Keep packages small and focused. A large package that holds unrelated definitions
becomes hard to maintain and creates unnecessary compile-order dependencies.

Packages may import from other packages:

```systemverilog
package alu_pkg;
    import bus_pkg::data_t;   // reuse the shared data type

    typedef enum logic [2:0] {
        ADD = 3'd0,
        SUB = 3'd1,
        AND = 3'd2,
        OR  = 3'd3,
        XOR = 3'd4
    } opcode_t;

endpackage
```

This builds a clear dependency graph: `alu_pkg` depends on `bus_pkg`, not on any
specific module.

## Common pitfalls

- **Defining types inside a module and expecting them to be visible elsewhere.**
  Types defined in a module body are local to that module. If another module needs
  the same type, move the definition to a package.
- **Relying on `$unit` for shared definitions.** Tool and file-ordering sensitivity
  makes `$unit` fragile. Use explicit packages.
- **Wildcard import collisions.** If two packages define `data_t`, a wildcard
  import of both causes an ambiguous name. Use qualified names or explicit imports
  to resolve the conflict.
- **Putting `always` blocks or module instances in a package.** Packages hold
  declarations only. Hardware behavior belongs in modules.
- **`parameter` vs `localparam` in a package.** Use `localparam` for constants
  that should not be overridden. Use `parameter` only if you intend to support
  parameterized package instantiation.

## Summary

- A `package` is a named namespace for shared types, parameters, and constants.
- Import with `import pkg::name` (explicit) or `import pkg::*` (wildcard);
  qualified names `pkg::name` need no import.
- Avoid `$unit`; prefer explicit packages for portability and clarity.
- One package per protocol or subsystem keeps dependencies clear and packages
  focused.

---

[← Enhanced Data Types](02-enhanced-data-types.md) · [Table of contents](../README.md) · [Next: Interfaces and Modports →](04-interfaces-and-modports.md)
