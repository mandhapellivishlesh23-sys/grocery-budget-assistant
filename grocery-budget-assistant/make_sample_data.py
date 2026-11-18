"""Regenerates the sample files in data/. Run it only if you want to reset them."""
import csv, json

ROWS = [
 # Sept: comfortably under budget
 ("2026-09-02","Milk 1L","dairy",62,4),("2026-09-02","Bread","bakery",45,2),
 ("2026-09-04","Basmati rice 5kg","pantry",640,1),("2026-09-05","Onions","produce",35,3),
 ("2026-09-05","Tomatoes","produce",40,2),("2026-09-07","Eggs (dozen)","dairy",84,2),
 ("2026-09-09","Chicken 1kg","meat",240,1),("2026-09-12","Paneer 200g","dairy",95,2),
 ("2026-09-14","Toor dal 1kg","pantry",165,2),("2026-09-16","Orange juice 1L","beverages",120,2),
 ("2026-09-19","Biscuits","snacks",30,5),("2026-09-21","Dish soap","household",110,1),
 ("2026-09-23","Bananas","produce",60,2),("2026-09-26","Cooking oil 1L","pantry",185,2),
 ("2026-09-28","Frozen peas","frozen",95,2),
 # Oct: blows the budget
 ("2026-10-01","Milk 1L","dairy",62,5),("2026-10-01","Atta 10kg","pantry",480,1),
 ("2026-10-03","Eggs (dozen)","dairy",84,3),("2026-10-04","Chicken 1kg","meat",240,2),
 ("2026-10-06","Mutton 500g","meat",420,2),("2026-10-08","Saffron 1g","pantry",450,1),
 ("2026-10-09","Apples","produce",180,2),("2026-10-11","Cheese slices","dairy",140,2),
 ("2026-10-13","Cashews 500g","snacks",560,1),("2026-10-15","Cold drinks 2L","beverages",95,6),
 ("2026-10-17","Ice cream","frozen",220,2),("2026-10-19","Detergent","household",390,1),
 ("2026-10-21","Pasta","pantry",110,3),("2026-10-24","Olive oil","pantry",750,1),
 ("2026-10-27","Chips","snacks",20,10),("2026-10-29","Yogurt","dairy",55,4),
 # Nov: edging into the warning zone, plus a few edge cases
 ("2026-11-01","Milk 1L","dairy",62,4),("2026-11-01","Basmati rice 5kg","pantry",650,1),
 ("2026-11-03","Onions","produce",38,3),("2026-11-03","Potatoes","produce",30,4),
 ("2026-11-05","Eggs (dozen)","dairy",84,2),("2026-11-06","Chicken 1kg","meat",250,1),
 ("2026-11-08","Bread","bakery",45,2),("2026-11-09","Toor dal 1kg","pantry",170,2),
 ("2026-11-10","Sugar 1kg","pantry",48,3),("2026-11-12","Tea 500g","beverages",260,1),
 ("2026-11-13","Paneer 200g","dairy",95,3),
 ("2026-11-14","Free sample sachet","snacks",0.01,1),      # boundary: lowest price
 ("2026-11-15","Water cans 20L","beverages",40,24),        # large quantity
 ("2026-11-16","Handwash","household",99,2),("2026-11-17","Fish 1kg","meat",380,1),
 ("2026-11-17","Dry fruits 1kg","snacks",900,1),
]

with open("data/sample_items.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["name", "category", "price", "quantity", "date"])
    for d, n, c, p, q in ROWS:
        w.writerow([n, c, p, q, d])

items = [{"id": i, "name": n, "category": c, "price": p, "quantity": q, "date": d}
         for i, (d, n, c, p, q) in enumerate(ROWS, 1)]
with open("data/sample_items.json", "w", encoding="utf-8") as f:
    json.dump({"version": 1, "budget": 6000.0, "items": items}, f, indent=2)

# a deliberately messy file to show off the row-by-row error log
bad = [
 ["name","category","price","quantity","date"],
 ["Mangoes","produce","150","2","2026-11-10"],
 ["","dairy","50","1","2026-11-10"],
 ["Butter","dairy","-20","1","2026-11-10"],
 ["Jam","pantry","abc","1","2026-11-10"],
 ["Ketchup","sauces","90","1","2026-11-10"],
 ["Noodles","pantry","15","0","2026-11-10"],
 ["Soap","household","40","2","10/11/2026"],
 ["Cereal","pantry","300","1","2031-01-01"],
 ["Lemons","produce","Rs. 10","6","2026-11-11"],
 ["Honey","pantry","320","1.5","2026-11-11"],
]
with open("data/sample_messy.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(bad)
print(len(ROWS), "sample rows written")
