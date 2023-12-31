import psycopg2
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.tree import export_text
from six import StringIO
from sklearn import tree
import pydotplus
from PIL import Image

# Parametri per la connessione al database PostgreSQL
db_params = {
    'host': 'localhost',
    'database': 'GDC',
    'user': 'postgres',
    'password': 'root',
    'port': 5433
}

# Connessione al database
connection = psycopg2.connect(**db_params)
cursor = connection.cursor()

# Query per estrarre i dati di addestramento dal database
query = """
(
    SELECT tpm, fpkm, fpkm_uq, unstranded, stranded_first, stranded_second, sample_type.type as tissue_label
    FROM gene_expression_file
    JOIN analysis_entity ON gene_expression_file.analysis = analysis_entity.analysis
    JOIN aliquote a ON analysis_entity.biospecimen_id = a.aliquote_id
    JOIN Analyte ay ON a.Analyte_Id = ay.analyte_id
    JOIN portion ON ay.portion_id = portion.Portion_Id
    JOIN sample s ON portion.sample_id = s.sample_id
    JOIN sample_type ON s.type = sample_type.type_id
    WHERE s.Type = 1 and gene_expression_file.gene = 'ENSG00000133703.13'
    LIMIT 10
)
UNION
(
    SELECT tpm, fpkm, fpkm_uq, unstranded, stranded_first, stranded_second, sample_type.type as tissue_label
    FROM gene_expression_file
    JOIN analysis_entity ON gene_expression_file.analysis = analysis_entity.analysis
    JOIN aliquote a ON analysis_entity.biospecimen_id = a.aliquote_id
    JOIN Analyte ay ON a.Analyte_Id = ay.analyte_id
    JOIN portion ON ay.portion_id = portion.Portion_Id
    JOIN sample s ON portion.sample_id = s.sample_id
    JOIN sample_type ON s.type = sample_type.type_id
    WHERE s.Type = 11 and gene_expression_file.gene = 'ENSG00000133703.13'
);
"""

query2 = """
    SELECT tpm, fpkm, fpkm_uq, unstranded, stranded_first, stranded_second, primary_site.site as tissue_label
    FROM gene_expression_file
    JOIN analysis_entity ON gene_expression_file.analysis = analysis_entity.analysis
    JOIN biospecimen ON analysis_entity.biospecimen_id = biospecimen.id
    JOIN "case" ON biospecimen."case" = "case".case_id
    JOIN primary_site ON "case".site = primary_site.site_id
    WHERE gene_expression_file.gene = 'ENSG00000133703.13' AND primary_site.site IN ('Brain', 'Skin', 'Pancreas', 'Bladder')
"""

# Esecuzione della query e ottenimento dei dati
cursor.execute(query2)
data = cursor.fetchall()
column_names = [desc[0] for desc in cursor.description]
df = pd.DataFrame(data, columns=column_names)

# Separazione dei dati in features (X) e target (y)
X = df.drop('tissue_label', axis=1)
y = df['tissue_label']

# Dividi i dati in set di addestramento e test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crea e addestra il modello di albero decisionale
model = DecisionTreeClassifier(random_state = 2, criterion = "entropy", min_samples_split=5)
model.fit(X_train, y_train)

# Valuta il modello
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

# Visualizza l'accuratezza e il report di classificazione
print(f'Accuratezza: {accuracy}')
print(f'Report di classificazione:\n{report}')

# Genera l'albero decisionale in formato testo
#tree_rules = export_text(model, feature_names=list(X.columns))
#print("Albero Decisionale:")
#print(tree_rules)

# Visualizza l'albero decisionale come grafico
dot_data = StringIO()
tree.export_graphviz(model, out_file=dot_data, feature_names=list(X.columns), class_names=['Brain', 'Skin', 'Pancreas', 'Bladder'], filled=True, node_ids=True, rounded=True, special_characters=True)
graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
graph.write_png("decision_tree.png")

# Visualizza l'immagine dell'albero
img = Image.open("decision_tree.png")
img.show()

# Chiudi la connessione al database
cursor.close()
connection.close()