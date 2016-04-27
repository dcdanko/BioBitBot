__Metagenomic Visualization Specification and Requirements__

- samples.txt
    Details of each sample in the analysis.
    + File with the name of each sample on separate lines
    + Sample names are expected to be in format <sample site>-<condition>-<replicate>

- taxa_hierarchy.txt
    Details of the taxonomic ranks under scrutiny.
    + File with names of line separated taxonomic ranks in order
    + First line is an integer specifying the offset of the first taxa from the root
    + One line may be a '-'
    + Lines following the '-' will be included in certain analysis but not used in the taxa hierarchy. This is useful for including host matches.

- aggregated_taxa.map
    Details of the taxonomic tree used during execution of the pipeline. Useful because it is far smaller than a complete taxonomy and because bacterial taxonomy tends to change often.
    + File with a tab-separated taxonomic path on each line
    + Starts with a header line stating the taxonomic rank of each column
    + Unknown columns should be filled with NA, including when greater resolution is unobtainable

- raw count files
- normalized count files
- alignment statistic files
    Detail the number of reads which aligned to each taxonomic rank for each sample.
    + Filename includes the sample name and taxonomic rank
    + Files contain a header line
    + File contains a single space separated content line in the form total_reads, reads_aligned, proportion_aligned.
    
- alpha diversity files
    Details the alpha diversity of every sample at a given taxonomic rank.
    + Filename contains the taxonomic rank
    + File contains a header line
    + Content lines are space separated in the format: sample_name, shannon_index
    + Files may contain other metrics after the shannon index. 
    
- differential count files
    Analysis of taxa which are differentially abundant between conditions.
    + Filename contains taxonomic rank
    + Columns are tab separated.
    + Contains a header line.
    + Fields are: "logFC"   "AveExpr"   "t" "P.Value"   "adj.P.Val" "B" "group1"    "group2"    "taxa"
    + If there are only two groups under comparison "group1" and "group2" may be ommitted but this is not recommended.


