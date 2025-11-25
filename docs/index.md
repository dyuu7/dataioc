# dataioc

**IoC for data in Python: declare what each value needs, resolve the graph on demand, and swap providers without changing downstream computations.**

`dataioc` describes a calculation as local derivation rules. Each builder requests only its direct dependencies; the container composes those requests into the graph needed by the result you ask for. There is no separate workflow to maintain.

## Start here

1. [Quickstart](quickstart.md): define local rules and request a result.
2. [Core concepts](concepts.md): understand descriptors, builders, and graph resolution.
3. [Providers](providers.md): bind a quantity to another source or derivation.
4. [Indexed data](indexed-data.md): reuse one model across related data groups.
5. [NumPy support](numpy.md): use `DataNDArray` with the optional NumPy integration.

## The model

```text
define local derivations
        |
bind data and providers
        |
request the result you need
        |
resolve only the required graph
```

Each derivation declares only its direct dependencies. The container composes them at runtime, evaluates what the requested result needs, and reuses successful values within that container.

Providers are chosen when the container is assembled, so a quantity can receive another source or derivation without changing the computations that consume it.

The core package has no mandatory numerical dependency. Install the `numpy` extra when using `DataNDArray`.

## Links

- [API reference](api.md)
- [GitHub repository](https://github.com/dyuu7/dataioc)
- [Contributors](https://github.com/dyuu7/dataioc#contributors)
