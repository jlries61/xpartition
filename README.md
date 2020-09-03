# xpartition
Exact Data Partitioner.  Randomly partitions a table into training, test, and holdout partitions, balanced on one or more fields.

## Prerequisites
`xpartition` is a [Python](https://www.python.org/) script, which is only expected to work under Python 3.  The following modules are required:

* [getopt](https://docs.python.org/3/library/getopt.html)

* [pandas](https://pandas.pydata.org/)

* [random](https://docs.python.org/3/library/random.html)

* [sys](https://docs.python.org/3/library/sys.html)

All but Pandas should be installed by default, but all can be installed with one's favorite package manager.  To install Pandas using Python's `pip` utility, type the following at the terminal:

```
$ pip3 install --user pandas
```

If you are running under Linux, chances are excellent that your distribution provides a Pandas package.  Check for it.

## What it does

Consider a data table in CSV format with an arbitrary number of records.  `xpartition` will shuffle the records randomly and then systematically assign then to the desired fields in the specified proportions.  The output data set (also in CSV format) will output the input table in the previous order, but including one or more indicator fields, specifying the assignment(s) for each record.  For example, one could partition the Boston Housing data set into learning and test partitions of equal sizes by issuing the following command:
```
$ xpartition BOSTON.CSV bpart.csv
```
The output data set, `bpart.csv`, would contain all of the fields of the input data set (BOSTON.CSV), plus a new one, `SAMPLE`, with two possible values: "Learn", if the record is part of the learning sample, and "Test" if it is to be part of the test sample.  A tabulation using [Salford Predictive Modeler](https://www.salford-systems.com/SPM) will show the numbers of records assigned to each to be exactly equal:
```
SAMPLE$                                       N      %  Cum %     Wgt Count      %  Cum %
 -----------------------------------------------------------------------------------------
 Learn                                       253  50.00  50.00           253  50.00  50.00
 Test                                        253  50.00 100.00           253  50.00 100.00
 -----------------------------------------------------------------------------------------
 Total                                       506        100.00           506        100.00
```

The reason why the numbers are exactly equal is that `xpartition` randomly shuffles the records and then alternately assigns records to the learning and test partitions before restoring the data to the original order.

To instead draw a 20% test sample, (four learning records per test record), one could specify the `--nlearn` and `--ntest` command line flags like so:
```
xpartition --nlearn=4 --ntest=1 BOSTON.CSV bpart2.csv
```
We tabulate `SAMPLE` on `bpart2.csv` and get:
```
 SAMPLE$                                       N      %  Cum %     Wgt Count      %  Cum %
 -----------------------------------------------------------------------------------------
 Learn                                       405  80.04  80.04           405  80.04  80.04
 Test                                        101  19.96 100.00           101  19.96 100.00
 -----------------------------------------------------------------------------------------
 Total                                       506        100.00           506        100.00
```

This time, `xpartition` assigns one record to the test sample for every four assigned to the learning sample.  Because 506 is not divisible by 5, there are not exactly four times as many learning sample records as test sample records, but the algorithm for making the assignments is exactly the same as before, guaranteeing as close to exact proportions as the numbers will permit.

When building CART, MARS, or TreeNet models, Salford Predictive Modeler (SPM) usually uses a test sample to "prune" a maximal model built on the learning sample in such a way that accuracy on the test sample is maximized.  But to measure model performance on completely independent data, one can also specify a holdout sample.  To do that in `xpartition`, specify the `--nholdout` flag, like so:
```
xpartition --nlearn=2 --ntest=1 --nholdout=1 BOSTON.CSV bpart3.csv
```
This time, one record each is assigned to the test and holdout samples for every two assigned to the learning sample.  `SAMPLE` tabulates as follows:
```
 SAMPLE$                                       N      %  Cum %     Wgt Count      %  Cum %
 -----------------------------------------------------------------------------------------
 Holdout                                     126  24.90  24.90           126  24.90  24.90
 Learn                                       254  50.20  75.10           254  50.20  75.10
 Test                                        126  24.90 100.00           126  24.90 100.00
 -----------------------------------------------------------------------------------------
 Total                                       506        100.00           506        100.00
```
CART, MARS, and TreeNet also support cross-validation, meaning that all data are used to build the model, but are partitioned into a certain number of "folds" (10 by default).  Then, one ancillary model is built per fold excluding that fold from the learning sample and each record is scored using the ancillary model it was not used to build in order to estimate the accuracy of the main model on independent data.

To partition `BOSTON.CSV` into ten cross validation folds, use the `--cv` flag as follows:
```
xpartition --cv=10 BOSTON.CSV bcv.csv
```
In this case, the shuffled records are assigned alternately to ten folds, repeating the process until the records are exhausted before the data are restored to their original order.  The new indicator variable is `CVFOLD`, which tabulates as follows:
```
 CVFOLD                           N      %  Cum %     Wgt Count      %  Cum %
 ----------------------------------------------------------------------------
 1                               51  10.08  10.08            51  10.08  10.08
 2                               51  10.08  20.16            51  10.08  20.16
 3                               51  10.08  30.24            51  10.08  30.24
 4                               51  10.08  40.32            51  10.08  40.32
 5                               51  10.08  50.40            51  10.08  50.40
 6                               51  10.08  60.47            51  10.08  60.47
 7                               50   9.88  70.36            50   9.88  70.36
 8                               50   9.88  80.24            50   9.88  80.24
 9                               50   9.88  90.12            50   9.88  90.12
 10                              50   9.88 100.00            50   9.88 100.00
 ----------------------------------------------------------------------------
 Total                          506        100.00           506        100.00
```

### Pipeline Mode

In addition to allowing the input and output data sets to be specified on the command line, `xpartition` can also read the input data from standard input and write the output data to standard output.  This is what will happen if there are no command line arguments.  If there is only one argument, it will be taken as the name of the input file and the output will be written to standard output.

### A Question of Balance

When preparing data for predictive modeling, it is usually a good idea to draw the samples in such a way that at least the dependent variable has as close as possible to the same distribution in each.  There may be other variables in the dataset for which this is particularly important.  `xpartition` supports this effort through the `--by` flag, which specifies a list of fields on which to balance.  These fields may be either categorical or continuous.  Either way, the records are first shuffled as before, and then sorted on the fields to be used for balancing before the partitioning is done.  Then, as usual, the records are returned to their original order.

The Boston housing dataset we have been using has a continuous target (`MV`), but we can still balance on it so that as much as possible, the distribution of MV is the same in both the learning and test samples.
```
xpartition --by=MV --nlearn=4 --ntest=1 BOSTON.CSV bosbal.csv
```

We then compute the descriptive statistics for `MV`, stratifying on `SAMPLE` and get:
```
 ============
 Variable: MV
 ============


 For Stratum: SAMPLE$ = "Learn"

                               Moments

 N                            405    Sum of Weights            405.00
 Mean                    22.50272    Sum                   9113.60000
 Std Deviation            9.19721    Variance                84.58858
 Skewness                 1.09668    Kurtosis                 1.47186
 Coeff Variation          0.40872    Std Error Mean           0.45701
 Cond. Mean              22.50272    N missing                      0
 N = 0                          0    N != 0                       405
```
```
 ============
 Variable: MV
 ============


 For Stratum: SAMPLE$ = "Test"

                               Moments

 N                            101    Sum of Weights            101.00
 Mean                    22.65347    Sum                   2288.00000
 Std Deviation            9.24158    Variance                85.40671
 Skewness                 1.13758    Kurtosis                 1.45401
 Coeff Variation          0.40795    Std Error Mean           0.91957
 Cond. Mean              22.65347    N missing                      0
 N = 0                          0    N != 0                       101
```

But balancing becomes more important if the dependent variable is categorical.  We can partition the Dorian Pyle credit data on its usual dependent variable (`BUYER`), like so:
```
xpartition --by=BUYER CREDIT.CSV credpart1.csv
```
