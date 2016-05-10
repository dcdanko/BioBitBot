#!/usr/bin/env python
"""
iBot is a tool to build interactive charts from your data. It is intended to allow users to easily 
access bioinformatics data analysis.

iBot is based on MultiQC by Phil Ewels. MultiQC is intended to provide quality control reports from 
a number of common bioinformatics tools aggregated into a single quality control report for a set of 
samples. iBot, extends this concept to data analysis. iBot combines a number of common data analysis
'modules' into single reports. The type of modules which are included in a report is based off of 
the type of experiment performed. 

As an example the 'microbiome' report type includes:
 - Principal Component Analysis of the samples
 - Phylogeny trees
 - MA and Volcano charts
 - and many more...

As an example of how data analytic modules work consider that the 'microarray' report includes the 
MA chart module and the PCA module but does not include the Phylogeny Tree module.

--- General documentation, repeated here for clarity.

iBot is intended to work in concert with a data analytic pipeline. The data analytics pipeline does 
all computationally intensive work. Ideally the analytics pipeline would output a series of chart 
ready data tables; in practice iBot does a fair amount of work to collate and lightly interpret the 
output of a pipeline. As a rough guide it should be possible to generate an iBot report in less than 
a minute on a desktop machine; any longer and one should consider offloading some computation to a 
pipeline.

Every iBot report type should include a specification stating the file types it requires to build a
report. Data-analytics module should include a specification (at least in the source code) stating 
the data type they expect. iBot is a research tool that is intended to quickly adapt to changing 
needs. 

It is perfectly acceptable to build a module type which is only intended to run in a single report 
type. Data analytics modules are NOT intended to be perfectly modular. While a smaller, less 
redundant codebase is easier to maintain a codebase which allows some redundancy (or 'reinventing 
the wheel') is often easier to extend and easier for novice programmers to understand. 

Proficient programmers should bear in mind that iBot is intended to support scientific research. 
Many bioinformaticians are relatively inexperienced programmers who need their code to 'Just Work'.
These contributions should be guided and checked but they should not be discouraged because they 
aren't written to a high standard. Inexperienced programmers should work to make sure their 
contributions are well documented above all.

iBot is actively supported and devloped. You can contact David Danko at dcdanko@gmail.com for help 
but the best way to get in touch is with an issue on github. In iBot there are no stupid questions.
"""

from setuptools import setup, find_packages

version = '0.6dev'

print("""-----------------------------------
 Installing iBot version {}
-----------------------------------

""".format(version))

setup(
    name = 'ibot',
    version = version,
    author = 'David Danko',
    author_email = 'dcdanko@gmail.com',
    description = "Create interactive visuals from your data.",
    long_description = __doc__,
    keywords = 'bioinformatics',
    url = 'http://kviz.kennedy.ox.ac.uk',
    download_url = '',
    license = 'GPLv3',
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    scripts = ['scripts/ibot'],
    install_requires = [
        'jinja2',
        'simplejson',
        'pyyaml',
        'click',
        'matplotlib'
    ],
    entry_points = {
        'ibot.analyses.v1': [
            'microarray = ibot.analyses.microarray:BaseIBotReport',
            'metagenomics = ibot.analyses.metagenomics:BaseIBotReport',
        ],
        'ibot.templates.v1': [
            'default = multiqc.templates.default',
            'default_dev = multiqc.templates.default_dev',
            'simple = multiqc.templates.simple',
            'geo = multiqc.templates.geo',
        ],
        # 'multiqc.cli_options.v1': [
            # 'my-new-option = myplugin.cli:new_option'
        # ],
        # 'multiqc.hooks.v1': [
            # 'execution_start = myplugin.hooks:execution_start',
            # 'config_loaded = myplugin.hooks:config_loaded',
            # 'before_modules = myplugin.hooks:before_modules',
            # 'after_modules = myplugin.hooks:after_modules',
            # 'execution_finish = myplugin.hooks:execution_finish',
        # ]
    },
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
)

print("""
--------------------------------
 iBot installation complete!
--------------------------------
""")
