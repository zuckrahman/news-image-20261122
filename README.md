# The World in One Day - 22 November 2026

[![News image 22 November 2026](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/c/news-image-20261122)
[![Rank](https://make.fun/badge/news-image-20261122/zuckrahman/news-image-20261122/rank.svg)](https://make.fun/c/news-image-20261122)
[![Reward](https://make.fun/badge/news-image-20261122/zuckrahman/news-image-20261122/reward.svg)](https://make.fun/c/news-image-20261122)

A newspaper front page that sums up the world news of Sunday 22 November 2026 in one image.

## The day

- **COP31 collapses in Antalya:** the climate talks end with no deal after the final text leaves out fossil fuels.
- **Russian warship hit in Benghazi:** suspected sea drones strike the corvette Merkury in the Libyan port.
- **Gulf standoff deepens:** Iran says two tankers hit mines east of the Strait of Hormuz.
- **Strike hits flats near Kyiv**, settler attacks are condemned in the West Bank, and at least 24 people die when a funeral boat capsizes in Nigeria.
- Also today: a Delta outage delays 1,600+ flights, Nepal's prime minister visits India, China eases margin rules, and a Thai court cuts a defamation sentence.

## How it works

`main.py` is a Python 3.13 program using only the standard library. It draws the 1024x1024 front page pixel by pixel, including its own bitmap font, and writes a deterministic PNG to `/output/entry.png`. It needs no network, and two runs write identical bytes.

Run it locally:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## License

MIT. See `LICENSE`.
