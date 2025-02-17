# -*- coding: utf-8 -*-
"""BigData.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1EtAQzALAncqACgi6TyaXHSuGQD4TDBp-
"""

!pip install pyspark

from pyspark.sql.functions import expr
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, isnan, when, count
from pyspark.ml.feature import PolynomialExpansion
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.feature import VectorIndexer
from pyspark.ml.feature import OneHotEncoder
from pyspark.ml.feature import StringIndexer
from pyspark.ml.feature import PolynomialExpansion

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

spark = SparkSession.builder.appName("Diamonds").getOrCreate()

data = spark.read.csv("diamonds.csv",
                      inferSchema = True, header = True)

data.show(5, truncate = False)

data = data.select(data.columns[1:])

data=data.dropna()
print(data.count())

from pyspark.sql.functions import col, isnan, when, count

# Count missing values in each column
missing_counts = data.select([count(when(isnan(c) | col(c).isNull(), c)).alias(c) for c in data.columns])
missing_counts.show()

# Validate 'cut' column against predefined categories
valid_cut_categories = ['Premium', 'Ideal', 'Good', 'Fair', 'Very Good']
data_filtered = data.filter(data['cut'].isin(valid_cut_categories))

data.printSchema()

data.groupBy("cut").count().show()

data.groupBy("clarity").count().show()

numeric_cols = [col for col, dtype in data.dtypes if dtype != "string"]
numeric_cols = [col for col in numeric_cols if col != "price"]

for col in numeric_cols:
    corr = data.corr(col, "price")
    print(f"The correlation between {col} and price is {round(corr, 2)}")

# Calculate correlation for each pair of numeric columns
correlations = {}
for col1 in numeric_cols:
    for col2 in numeric_cols:
        corr_value = data.corr(col1, col2)
        if col1 not in correlations:
            correlations[col1] = {}
        correlations[col1][col2] = corr_value

# Convert the correlation dictionary to a pandas DataFrame
corr_matrix = pd.DataFrame(correlations)

# Add the correlation of each numeric column with the price
price_corr = [data.corr(col, "price") for col in numeric_cols]
corr_matrix["price"] = price_corr
corr_matrix.loc["price"] = price_corr + [1.0]

# Print the correlation matrix
print(corr_matrix)

# Plot the correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
plt.title("Correlation Matrix")
plt.show()

string_cols = [col for col, dtype in data.dtypes if dtype == "string"]

for col in string_cols:
    print(f"Relationships for the column {col}")
    data.groupBy(col).agg({"price": "mean"}).show()
    print("------------------------------------------------------")

for col in numeric_cols:
    print(f"For col {col}")
    avg_value = round(data.select(expr(f"AVG({col})")).collect()[0][0], 2)
    std_value = round(data.select(expr(f"STD({col})")).collect()[0][0], 2)
    data.select(expr(f"(ABS({col} - {avg_value}) / {std_value}) > 3").alias("z_score")).groupBy("z_score").count().show()

df = data.groupBy("cut").count().toPandas()
df

# @title count

from matplotlib import pyplot as plt
df['count'].plot(kind='line', figsize=(8, 4), title='count')
plt.gca().spines[['top', 'right']].set_visible(False)

# @title count

from matplotlib import pyplot as plt
df['count'].plot(kind='hist', bins=20, title='count')
plt.gca().spines[['top', 'right',]].set_visible(False)

# @title cut

from matplotlib import pyplot as plt
import seaborn as sns
df.groupby('cut').size().plot(kind='barh', color=sns.palettes.mpl_palette('Dark2'))
plt.gca().spines[['top', 'right',]].set_visible(False)

sns.barplot(data = df, x = "cut", y = "count")

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.feature import VectorIndexer
from pyspark.ml.feature import OneHotEncoder
from pyspark.ml.feature import StringIndexer

string_cols

for col in string_cols:
    indexer = StringIndexer(inputCol = f"{col}", outputCol = f"{col}Index")
    encoder = OneHotEncoder(inputCol = f"{col}Index", outputCol = f"{col}Vec")
    data = indexer.fit(data).transform(data)
    data = encoder.fit(data).transform(data)

data.show()

from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression

cols_keeps = numeric_cols + [col for col in data.columns if "vec" in col.lower()]

assembler = VectorAssembler(inputCols = cols_keeps,
                            outputCol = "features")

output = assembler.transform(data)

train, test = output.randomSplit(weights = [0.7, 0.3], seed = 42)

lr = LinearRegression(featuresCol = "features", labelCol = "price", predictionCol = "prediction")

model = lr.fit(train)

predictions = model.evaluate(test)

print("RMSE: {}".format(predictions.rootMeanSquaredError))
print("MSE: {}".format(predictions.meanSquaredError))
print("r2: {}".format(predictions.r2))

predictions_df = predictions.predictions.select("price", "prediction").toPandas()

predictions_df.plot.scatter(x = "price", y = "prediction")

# Polynomial expansion
from pyspark.ml.feature import PolynomialExpansion
polyExpansion = PolynomialExpansion(degree=2, inputCol="features", outputCol="polyFeatures")
polyOutput = polyExpansion.transform(output)

# Split data into training and testing sets
train, test = polyOutput.randomSplit(weights=[0.7, 0.3], seed=42)

# Train linear regression model
lr = LinearRegression(featuresCol="polyFeatures", labelCol="price", predictionCol="prediction")
model = lr.fit(train)

# Evaluate the model
predictions = model.evaluate(test)
print("RMSE: {}".format(predictions.rootMeanSquaredError))
print("MSE: {}".format(predictions.meanSquaredError))
print("r2: {}".format(predictions.r2))

# Plot predictions vs actual prices
predictions_df = predictions.predictions.select("price", "prediction").toPandas()
predictions_df.plot.scatter(x="price", y="prediction")
plt.show()

# Plot predictions vs actual prices
predictions_df = predictions.predictions.select("price", "prediction").toPandas()
predictions_df.plot.scatter(x="price", y="prediction")
plt.xlabel("Actual Price")
plt.ylabel("Predicted Price")
plt.title("Actual vs Predicted Prices")
plt.show()