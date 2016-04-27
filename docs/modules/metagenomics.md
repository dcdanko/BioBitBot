__Metagenomic Visualization Specification and Requirements__

- samples.txt
    + file with the name of each sample on separate lines
    + sample names are expected to be in format <sample site>-<condition>-<replicate>

- taxa_hierarchy.txt
    + file with names of line separated taxonomic ranks in order
    + first line is an integer specifying the offset of the first taxa from the root

- aggregated_taxa.map
    + file with a tab-separated taxonomic path on each line
    + starts with a header line stating the taxonomic rank of each column
    + unknown columns should be filled with NA, including when greater resolution is unobtainable

- raw count files
- normalized count files
- alignment statistic files
- alpha diversity files
- differential count files


