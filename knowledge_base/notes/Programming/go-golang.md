# Go (Golang) Programming Notes

> [← Back to Main Index](README.md)

## Table of Contents

- [Introduction & Language Characteristics](#introduction--language-characteristics)
  - [Package & Import Declarations](#package--import-declarations)
- [Installation & Environment Variables](#installation--environment-variables)
  - [Installing Go Over SSH](#installing-go-over-ssh)
- [Go CLI Basic Commands & `fmt` Verbs](#go-cli-basic-commands--fmt-verbs)
  - [Core `go` Commands](#core-go-commands)
  - [`fmt` Format Verbs & Escape Characters](#fmt-format-verbs--escape-characters)
- [Basic Concepts & Package Organization](#basic-concepts--package-organization)
  - [Base Formatting with `fmt.Printf`](#base-formatting-with-fmtprintf)
  - [Creating & Importing a Custom Package (`stringutil`)](#creating--importing-a-custom-package-stringutil)
- [Remainder Operator (`%`)](#remainder-operator-)
- [Loops & Printing](#loops--printing)
- [Variables & Constants](#variables--constants)
  - [Declaring & Initializing Variables](#declaring--initializing-variables)
  - [Constants & `iota`](#constants--iota)
  - [Bitwise Operations with `iota`](#bitwise-operations-with-iota)
- [Scopes, Closures & Wrapper Functions](#scopes-closures--wrapper-functions)
- [Memory Addresses & Pointers](#memory-addresses--pointers)
  - [Referencing (`&`), Dereferencing (`*`) & Reassigning](#referencing--dereferencing---reassigning)
  - [Why Use Pointers in Go?](#why-use-pointers-in-go)
  - [Complete Pointer Example](#complete-pointer-example)

---

## Introduction & Language Characteristics

- **Compiled & Cross-Platform:** Go 1.5+ supports native cross-compilation out of the box. For example, on macOS you can set `GOOS=linux GOARCH=amd64 go build` to compile a Linux binary; on Windows, configure `GOOS` and `GOARCH` similarly.
- **Paradigm:** Procedural, concurrent, and object-oriented (via structs, interfaces, and methods), where procedures/functions are composed into a complete program.
- **Hardware & Concurrency:** Native support for multi-core processors and lightweight concurrency.
- **Networking & Server-Side:** Network-oriented and capable of handling high-performance backend/server workloads (similar to or replacing Node.js server-side use cases).
- **Memory Management:** Automatic garbage collection with clean syntax bridging scripting ergonomics and low-level systems performance.
- **Semicolons:** Automatically inserted by the compiler (explicit semicolons are only needed when placing multiple statements on a single line).

### Package & Import Declarations

1. **First line (`package`):**
   Every Go file starts with a package declaration (e.g., `package main` for an executable entrypoint). Code can be organized into folders by purpose (`crypto`, `system`, `network`, `webapp`, etc.).
2. **Second line (`import`):**
   Imports pre-existing functions and packages from the Go standard library ([golang.org/pkg/#stdlib](https://golang.org/pkg/#stdlib)) or third-party repositories ([pkg.go.dev / godoc.org](https://pkg.go.dev/)).
   - *Tip:* In standard library URLs, replacing `pkg` with `src` lets you browse the package's source code directly.
   - `fmt.Println`: `fmt` is the package and `Println` prints content followed by a newline (`Print` prints without adding a trailing newline).
3. **No Code Pollution:**
   Go enforces strict hygiene—unused imports or variables result in a compilation error. Use what you import, or don't import it at all.

```go
// Single import
import "fmt"

// Grouped import
import (
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)
```

---

## Installation & Environment Variables

| Variable / Command | Purpose |
| :--- | :--- |
| `GOROOT` | Path where Go itself is installed (only needed if installed in a non-default location) |
| `GOPATH` | Path pointing to your Go workspace (`src`, `pkg`, `bin`) |
| `GOBIN` | Path pointing to the `bin` directory inside your Go workspace |
| `go help <command>` | Built-in CLI documentation (e.g., `go help environment`) |

**Set Go binary `PATH` system-wide in `/etc/profile`:**

```bash
export PATH=$PATH:/usr/local/go/bin
```

**Set user workspace variables in `~/.profile`:**

```bash
export GOPATH=$HOME/workspaces/gocode
export PATH=$HOME/workspaces/gocode/bin:$PATH
```

*(Appending `:$PATH` preserves existing system binary paths.)*

### Installing Go Over SSH

Download and extract a Go release tarball remotely over SSH (adjust host and Go version as needed):

```bash
ssh root@debsrv05s 'cd /usr/local && \
  wget https://storage.googleapis.com/golang/go1.8.1.linux-amd64.tar.gz && \
  tar -xzvf go1.8.1.linux-amd64.tar.gz && \
  go version && \
  rm -f go1.8.1.linux-amd64.tar.gz'
```

---

## Go CLI Basic Commands & `fmt` Verbs

### Core `go` Commands

| Command | Behavior |
| :--- | :--- |
| `go run <file.go>` | Compiles and runs a `.go` file directly (e.g., `go run main.go`). |
| `go build` | **Executable (`package main`):** Compiles the program, reports any errors, and outputs the binary in the current folder.<br>**Library package:** Compiles to check for errors and discards the resulting artifact. |
| `go install` | **Executable:** Compiles the program, names the binary after the parent folder, and places it in `$GOPATH/bin`.<br>**Library package:** Compiles the package into an archive file (`.a`) and places it in `$GOPATH/pkg`. |
| `go clean` | Removes object files and cached build artifacts from package source directories. |

### `fmt` Format Verbs & Escape Characters

| Verb / Escape | Description |
| :---: | :--- |
| `%#x` / `%#X` | Hexadecimal (lowercase / uppercase) with `0x` / `0X` prefix |
| `%d` | Base-10 decimal integer |
| `%b` | Base-2 binary representation |
| `%f` | Floating-point number |
| `%q` | Single-quoted character literal or double-quoted string safely escaped with Go syntax |
| `%T` | Type of the value |
| `%v` | Value in its default format |
| `\t` | Horizontal tab |
| `\n` | Newline |

---

## Basic Concepts & Package Organization

### Base Formatting with `fmt.Printf`

```go
package main

import "fmt"

func main() {
	// Decimal (%d), Binary (%b), Hexadecimal (%#x) separated by tabs (\t)
	fmt.Printf("%d \t %b \t %#x \n", 2048, 2048, 2048)
}
```

### Creating & Importing a Custom Package (`stringutil`)

Directory layout inside `$GOPATH/src`:

```text
~/Workspaces/gocode/src/github/go-lang-training$ ls -lR first_package/
first_package/:
main
stringutil

first_package/main:
main.go

first_package/stringutil:
name.go
reverse.go
reverseTwo.go
```

**`first_package/main/main.go`:**

```go
package main

import (
	"fmt"
	"github.com/t0m-a/golangex/firstPackage/stringutil"
)

func main() {
	fmt.Println(stringutil.Reverse("!og, og, oG !olleH"))
	fmt.Println(stringutil.MyName, stringutil.MyPlace)
}
```

**`first_package/stringutil/name.go`:**

```go
package stringutil

// MyName is exported (starts with a capital letter)
var MyName = "Tom"

// MyPlace is exported with assigned value "@127.0.0.1"
var MyPlace = "@127.0.0.1"
```

**`first_package/stringutil/reverse.go`:**

```go
// Package stringutil contains utility functions for working with strings.
package stringutil

// Reverse returns its argument string reversed rune-by-rune via reverseTwo.
func Reverse(s string) string {
	return reverseTwo(s)
}
```

**`first_package/stringutil/reverseTwo.go`:**

```go
package stringutil

// reverseTwo is unexported (package-private) because it starts with a lowercase letter.
func reverseTwo(s string) string {
	r := []rune(s)
	for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
		r[i], r[j] = r[j], r[i]
	}
	return string(r)
}
```

---

## Remainder Operator (`%`)

The `%` operator computes the remainder of integer division (useful for checking whether a number is odd or even):

```go
package main

import "fmt"

func main() {
	// 4 divided by 2 equals 2 with a remainder of 0
	quotient := 4 / 2
	fmt.Printf("%d \t", quotient)
	fmt.Println(&quotient)

	remainder := 4 % 2
	fmt.Printf("%d \t", remainder)
	fmt.Println(&remainder)

	// 5 divided by 2 equals 2 with a remainder of 1
	quotient2 := 5 / 2
	fmt.Printf("%d \t", quotient2)
	fmt.Println(&quotient2)

	remainder2 := 5 % 2
	fmt.Printf("%d \t", remainder2)
	fmt.Println(&remainder2)

	// How many times does 3 fit into 4999? (1666 times, remainder 1)
	var quotient3 float32
	quotient3 = 4999 / 3
	fmt.Printf("%f \t", quotient3) // %f formats floating-point numbers
	fmt.Println(&quotient3)

	var remainder3 float32
	remainder3 = 4999 % 3
	fmt.Printf("%f \t", remainder3)
	fmt.Println(&remainder3)
}
```

---

## Loops & Printing

Print numbers `0` through `199` in decimal, binary, hexadecimal, and quoted character (`%q`) formats:

```go
package main

import "fmt"

func main() {
	for i := 0; i < 200; i++ {
		fmt.Printf("%d \t %b \t %x \t %q \n", i, i, i, i)
	}
}
```

---

## Variables & Constants

### Declaring & Initializing Variables

- A variable declared without an explicit value is initialized to its **zero value** (`0` for numeric types, `""` for strings, `false` for booleans).
- Two primary declaration styles:
  1. **Short declaration (`:=`)** — *Only usable inside a function (`func`).*
  2. **`var` keyword** — Usable at package level or function level.

**`declare_and_initialize/main.go`:**

```go
package main

import "fmt"

func main() {
	// Variable declarations with explicit types (initialized to zero values)
	var a int     // integer
	var b string  // string
	var c float64 // 64-bit floating-point number (uses '.' as decimal point)
	var d bool    // boolean (true or false)

	// Multiple variable declaration and assignment on one line
	var e, f string = "je suis le contenu de la var e", "je suis le contenu de la var f"

	// Assigning values to previously declared variables
	a = 7
	b = "couscous"
	c = 3.1415
	d = true

	// %T prints the variable's Type
	fmt.Println("Displaying the type (%T) of each variable:")
	fmt.Printf("%T \n", a)
	fmt.Printf("%T \n", b)
	fmt.Printf("%T \n", c)
	fmt.Printf("%T \n", d)
	fmt.Printf("%T \n", e)
	fmt.Printf("%T \n", f)

	// %v prints the variable's Value in its default format
	fmt.Println("Displaying the value (%v) of each variable:")
	fmt.Printf("%v \n", a)
	fmt.Printf("%v \n", b)
	fmt.Printf("%v \n", c)
	fmt.Printf("%v \n", d)
	fmt.Printf("%v \n", e)
	fmt.Printf("%v \n", f)

	// Display both Type (%T) and Value (%v) on the same line aligned with tabs (\t)
	fmt.Println("Displaying both type (%T) and value (%v) on the same line:")
	fmt.Printf("%T \t \t \t %v \n", a, a)
	fmt.Printf("%T \t \t \t %v \n", b, b)
	fmt.Printf("%T \t \t %v \n", c, c)
	fmt.Printf("%T \t \t \t %v \n", d, d)
	fmt.Printf("%T \t \t \t %v \n", e, e)
	fmt.Printf("%T \t \t \t %v \n", f, f)
}
```

### Constants & `iota`

Constants (`const`) hold immutable values known at compile time. `iota` is Go's built-in successive untyped integer constant generator, which resets to `0` at each new `const (` block.

```go
package main

import "fmt"

const p string = "granit"
const r = 4096.556

// Declaring multiple constants in a block
const (
	pi       = "3,1415"
	pi2      = 3.1415
	language = "Go lang! GO !"

	// L is exported (starts with a capital letter); doc comments on exported identifiers
	// should begin with the identifier's name to satisfy golint.
	L = "see what Go says when using a Capital Letter as the first letter"

	// iota increments for each constant specification in the const block (pi=0, pi2=1, language=2, L=3)
	whatsaniota       = iota // 4
	thisisaniota      = iota // 5
	incaseyoumissedit = iota // 6
)

const (
	x = iota // 0 — iota resets in a new const block
	y = iota // 1
)

const (
	_ = iota      // 0 ignored using the blank identifier (_)
	g = iota * 10 // 1 * 10 = 10
	h = iota * 10 // 2 * 10 = 20
	i = g * h     // 200 — constants can be multiplied together
	k = i * i     // 40000
)

func main() {
	const q = 42
	const s = "3,1415"
	const t bool = false

	fmt.Println("p - ", p)
	fmt.Println("q - ", q)
	fmt.Println("r - ", r)
	fmt.Println("s - ", s)
	fmt.Println("t - ", t)
	fmt.Println("Pi the \"European way\" \t - ", pi)
	fmt.Println("Pi the \"US\" way \t - ", pi2)
	fmt.Println("Language is - \t \t", language)
	fmt.Println("L - ", L)
	fmt.Println("whatsaniota - ", whatsaniota)
	fmt.Println("thisisaniota - ", thisisaniota)
	fmt.Println("incaseyoumissedit - ", incaseyoumissedit)
	fmt.Println("x - ", x)
	fmt.Println("y - ", y)
	fmt.Println("g - ", g)
	fmt.Println("h - ", h)
	fmt.Println("i - ", i)
	fmt.Println("k - ", k)
}
```

### Bitwise Operations with `iota`

Using bit shifting (`<<`) with `iota` to define byte-size constants (`KB`, `MB`, `GB`, `TB`):

```go
package main

import "fmt"

const (
	_  = iota             // 0 ignored
	kb = 1 << (iota * 10) // 1 << (1 * 10) = 1024 (2^10)
	mb = 1 << (iota * 10) // 1 << (2 * 10) = 1,048,576 (2^20)
	gb = 1 << (iota * 10) // 1 << (3 * 10) (2^30)
	tb = 1 << (iota * 10) // 1 << (4 * 10) (2^40)
)

func main() {
	fmt.Println("binary\t\t\t\t\t\t\tdecimal")
	fmt.Printf("%b\t\t\t\t\t\t%d\n", kb, kb)
	fmt.Printf("%b\t\t\t\t\t%d\n", mb, mb)
	fmt.Printf("%b\t\t\t\t%d\n", gb, gb)
	fmt.Printf("%b\t\t%d\n", tb, tb)
}
```

---

## Scopes, Closures & Wrapper Functions

`wrapper` returns an anonymous function (`func() int`) that closes over the outer-scope variable `x`:

```go
package main

import "fmt"

/*
wrapper returns a function as a value.
x := 0 is declared in the outer scope of wrapper(), so its state is remembered
across calls to the returned inner closure function.
*/
func wrapper() func() int {
	x := 0
	return func() int {
		x++
		return x
	}
}

func main() {
	increment := wrapper()   // Assign the returned anonymous function (func expression)
	fmt.Println(increment()) // 1
	fmt.Println(increment()) // 2
}
```

---

## Memory Addresses & Pointers

### Referencing (`&`), Dereferencing (`*`) & Reassigning

- **`&` (Address-of operator):** `&a` yields the memory address where the value of variable `a` is stored.
- **`*int` (Pointer type):** A type representing a pointer to an `int` memory address.
- **`*` (Dereference operator):** Placing `*` in front of a pointer variable (`*bee`) dereferences the pointer, returning or modifying the actual value stored at that memory address.

```go
a := 43
var bee *int = &a // Referencing: bee is of type *int and holds the memory address of a
```

Reassigning the value through the dereferenced pointer updates `a` directly:

```go
*bee = 42       // Dereferencing and reassigning the value at &a to 42
fmt.Println(a)  // Prints: 42
```

### Why Use Pointers in Go?

- We can pass a compact memory address (reference) instead of copying large data structures.
- Functions can mutate the value stored at a memory address directly.
- **Everything in Go is PASS BY VALUE**—when you pass a pointer, you are passing the memory address by value.

### Complete Pointer Example

```go
package main

import "fmt"

// Package-scope variables (if capitalized, e.g., 'A', they would be exported outside the package)
var a = 3
var b = 4
var c *int = &a // Referencing: c points to the memory address of a (&a == c, *c == a)
var d *int = &b // Go can also infer the type *int automatically via: var d = &b

func showofa() {
	fmt.Println(&a, "\t", a)
	fmt.Println(*c) // Dereferencing pointer c to get the actual value of a (3)
}

func showofb() {
	fmt.Println(&b, "\t", b)
	fmt.Println(*d)
}

func main() {
	var result int
	result = a * b

	showofa()
	showofb()

	fmt.Println(result, "\t \t", &result)

	// Reassign the value stored at *c (which is variable a) to 2
	*c = 2

	var newresult int
	newresult = a * b
	fmt.Println(a)                        // 2
	fmt.Println(newresult, "\t \t", &newresult) // 8
}
```
