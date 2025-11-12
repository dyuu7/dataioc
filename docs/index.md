# dataioc

**Declarative data dependencies and on-demand computation for Python.**

dataioc lets you define data through reusable derivation rules. Request a result, and the container resolves its dependencies and caches the values it builds. Data providers can be configured independently of the computations that consume them.

## Start here

1. [Quickstart](quickstart.md): define one derived value.
2. [Core concepts](concepts.md): understand descriptors and builders.
3. [Providers](providers.md): replace a data source or computation.
4. [Indexed data](indexed-data.md): reuse one model across data groups.
5. [NumPy support](numpy.md): use `DataNDArray` with NumPy 1.26 and 2.x.

## The model

```text
declare a derivation
        |
request a result
        |
resolve dependencies on demand
        |
cache constructed values
```

The core package has no mandatory numerical dependency. Install the `numpy` extra when using `DataNDArray`.

## Links

- [API reference](api.md)
- [GitHub repository](https://github.com/dyuu7/dataioc)
- [Contributors](https://github.com/dyuu7/dataioc#contributors)
