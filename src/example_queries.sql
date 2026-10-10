-- 1. Most common precursors used across all recipes
SELECT material, COUNT(*) AS uses
FROM precursors
GROUP BY material
ORDER BY uses DESC
LIMIT 15;

-- 2. Recipes that produced nanorods, with their precursors
SELECT r.paragraph_id, r.text_snippet, p.material, p.amount
FROM recipes r
JOIN precursors p ON r.paragraph_id = p.paragraph_id
WHERE r.paragraph_id IN (
    SELECT paragraph_id FROM characterization WHERE morphologies LIKE '%rod%'
)
LIMIT 20;

-- 3. Seed-mediated vs seedless recipe counts by year
SELECT a.year, r.seed_mediated, COUNT(*) AS n
FROM recipes r
JOIN articles a ON r.doi = a.doi
WHERE a.year IS NOT NULL
GROUP BY a.year, r.seed_mediated
ORDER BY a.year;

-- 4. Recipes using both CTAB and AgNO3 (known nanorod-shape-control combo)
SELECT DISTINCT r.paragraph_id, r.text_snippet
FROM recipes r
WHERE r.paragraph_id IN (SELECT paragraph_id FROM precursors WHERE material LIKE '%CTAB%')
  AND r.paragraph_id IN (SELECT paragraph_id FROM precursors WHERE material LIKE '%AgNO3%')
LIMIT 10;

-- 5. Most-cited articles that contain a synthesis recipe
SELECT a.doi, a.citations, a.year, COUNT(r.paragraph_id) AS recipe_paragraphs
FROM articles a
JOIN recipes r ON a.doi = r.doi
GROUP BY a.doi
ORDER BY a.citations DESC
LIMIT 10;
