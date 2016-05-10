# [<img src="http://www.kennedy.ox.ac.uk/@@primary-logo" width="250" title="KIR">](http://www.kennedy.ox.ac.uk/)

iBot is a tool to build interactive charts from your data. It is intended to allow users to easily access bioinformatics data analysis.

iBot is based on MultiQC by Phil Ewels. MultiQC is intended to provide quality control reports from a number of common bioinformatics tools aggregated into a single quality control report for a set of samples. iBot extends this concept to data analysis. iBot combines a number of common data analysis 'modules' into single reports. The type of modules which are included in a report is based off of the type of experiment performed. 

As an example the 'microbiome' report type includes:
 - Principal Component Analysis of the samples
 - Phylogeny trees
 - MA and Volcano charts
 - and many more...

As an example of how data analytic modules work consider that the 'microarray' report includes the MA chart module and the PCA module but does not include the Phylogeny Tree module.

--

iBot is intended to work in concert with a data analytic pipeline. The data analytics pipeline does all computationally intensive work. Ideally the analytics pipeline would output a series of chart ready data tables; in practice iBot does a fair amount of work to collate and lightly interpret the 
output of a pipeline. As a rough guide it should be possible to generate an iBot report in less than a minute on a desktop machine; any longer and one should consider offloading some computation to a pipeline.

Every iBot report type should include a specification stating the file types it requires to build areport. Data-analytics module should include a specification (at least in the source code) stating the data type they expect. iBot is a research tool that is intended to quickly adapt to changing needs. 

It is perfectly acceptable to build a module type which is only intended to run in a single report type. Data analytics modules are NOT intended to be perfectly modular. While a smaller, less redundant codebase is easier to maintain a codebase which allows some redundancy (or 'reinventing the wheel') is often easier to extend and easier for novice programmers to understand. 

Proficient programmers should bear in mind that iBot is intended to support scientific research. Many bioinformaticians are relatively inexperienced programmers who need their code to 'Just Work'. These contributions should be guided and checked but they should not be discouraged because they aren't written to a high standard. Less experienced programmers should work to make sure their contributions are well documented above all.

iBot is actively supported and devloped. You can contact David Danko at dcdanko@gmail.com for help but the best way to get in touch is with an issue on github. In iBot there are no stupid questions.

--

Terminology:
- analysis, a collection of modules for a certain type of pipeline ouput. E.G. uarray, ubiome. 
- module, a cohesive piece of data analysis. E.G. significance plots, PCA
- report, the single html file which is the tangible result of an analysis
- pipeline, a seperate piece of software that produces data files which iBot can interpret.

In iBot analyses and modules share the role of modules in MultiQC

Deprecated Terminology:
iBot is based on MultiQC and is very actively developed. A number of terms may show up in the codebase which are no longer relevant to the function of iBot.
- sname, or sample name

--

iBot was originally developed (from MultiQC!) at the Kennedy Institute of Rheumatology at Oxford. The work was supported by Dr. Nicholas Ilott and Prof. Fiona Powrie. At present David Danko has done the majority of work to modify MultiQC into iBot.