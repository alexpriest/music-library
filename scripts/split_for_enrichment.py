import json, os
lib = json.load(open("data/books.json"))
books = lib["books"]

# weight: real song count, but reserve capacity for canonical-fill books
def weight(b):
    if b["fill_canonical"]:
        return max(b["song_count_captured"], 18)
    return max(b["song_count_captured"], 2)

N = 14
groups = [[] for _ in range(N)]
loads = [0]*N
# greedy longest-processing-time bin packing
for b in sorted(books, key=weight, reverse=True):
    i = loads.index(min(loads))
    groups[i].append(b)
    loads[i] += weight(b)

os.makedirs("data/enrich_in", exist_ok=True)
os.makedirs("data/enriched", exist_ok=True)
for i, g in enumerate(groups, 1):
    json.dump({"group": f"{i:02d}", "books": g}, open(f"data/enrich_in/group-{i:02d}.json","w"),
              indent=2, ensure_ascii=False)
    titles = ", ".join(b["title"][:28] for b in g)
    print(f"group-{i:02d}: {len(g):2d} books, ~{loads[i-1]:3d} songs | {titles}")
