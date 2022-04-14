// ===========================================================================
//
//                            PUBLIC DOMAIN NOTICE
//            National Center for Biotechnology Information (NCBI)
//
//  This software/database is a "United States Government Work" under the
//  terms of the United States Copyright Act. It was written as part of
//  the author's official duties as a United States Government employee and
//  thus cannot be copyrighted. This software/database is freely available
//  to the public for use. The National Library of Medicine and the U.S.
//  Government do not place any restriction on its use or reproduction.
//  We would, however, appreciate having the NCBI and the author cited in
//  any work or product based on this material.
//
//  Although all reasonable efforts have been taken to ensure the accuracy
//  and reliability of the software and data, the NLM and the U.S.
//  Government do not and cannot warrant the performance or results that
//  may be obtained by using this software or data. The NLM and the U.S.
//  Government disclaim all warranties, express or implied, including
//  warranties of performance, merchantability or fitness for any particular
//  purpose.
//
// ===========================================================================
//
// File Name:  xtract.go
//
// Author:  Jonathan Kans
//
// ==========================================================================

package main

import (
	"bufio"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"github.com/fatih/color"
	"github.com/gedex/inflector"
	"github.com/klauspost/cpuid"
	"github.com/pbnjay/memory"
	"github.com/surgebase/porter2"
	"html"
	"io"
	"math"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"runtime/pprof"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
)

// XTRACT VERSION AND HELP MESSAGE TEXT

const xtractVersion = "13.9"

const xtractHelp = `
Overview

  Xtract uses command-line arguments to convert XML data into a tab-delimited table.

  -pattern places the data from individual records into separate rows.

  -element extracts values from specified fields into separate columns.

  -group, -block, and -subset limit element exploration to selected XML subregions.

Processing Flags

  -strict          Remove HTML and MathML tags
  -mixed           Allow mixed content XML

  -accent          Excise Unicode accents and diacritical marks
  -ascii           Unicode to numeric HTML character entities
  -compress        Compress runs of spaces

  -stops           Retain stop words in selected phrases

Data Source

  -input           Read XML from file instead of stdin
  -transform       File of substitutions for -translate

Exploration Argument Hierarchy

  -pattern         Name of record within set
  -group             Use of different argument
  -block               names allows command-line
  -subset                control of nested looping

Path Navigation

  -path            Explore by list of adjacent object names

Exploration Constructs

  Object           DateRevised
  Parent/Child     Book/AuthorList
  Path             MedlineCitation/Article/Journal/JournalIssue/PubDate
  Heterogeneous    "PubmedArticleSet/*"
  Exhaustive       "History/**"
  Nested           "*/Taxon"
  Recursive        "**/Gene-commentary"

Conditional Execution

  -if              Element [@attribute] required
  -unless          Skip if element matches
  -and             All tests must pass
  -or              Any passing test suffices
  -else            Execute if conditional test failed
  -position        [first|last|outer|inner|even|odd|all]

String Constraints

  -equals          String must match exactly
  -contains        Substring must be present
  -is-within       String must be present
  -starts-with     Substring must be at beginning
  -ends-with       Substring must be at end
  -is-not          String must not match
  -is-before       First string < second string
  -is-after        First string > second string
  -matches         Matches without commas or semicolons
  -resembles       Requires all words, but in any order

Object Constraints

  -is-equal-to     Object values must match
  -differs-from    Object values must differ

Numeric Constraints

  -gt              Greater than
  -ge              Greater than or equal to
  -lt              Less than
  -le              Less than or equal to
  -eq              Equal to
  -ne              Not equal to

Format Customization

  -ret             Override line break between patterns
  -tab             Replace tab character between fields
  -sep             Separator between group members
  -pfx             Prefix to print before group
  -sfx             Suffix to print after group
  -rst             Reset -sep through -elg
  -clr             Clear queued tab separator
  -pfc             Preface combines -clr and -pfx
  -deq             Delete and replace queued tab separator
  -def             Default placeholder for missing fields
  -lbl             Insert arbitrary text

XML Generation

  -wrp             Wrap elements in XML object
  -plg             Prologue to print before elements
  -elg             Epilogue to print after elements
  -fwd             Foreword to print before set
  -awd             Afterword to print after set

Element Selection

  -element         Print all items that match tag name
  -first           Only print value of first item
  -last            Only print value of last item
  -NAME            Record value in named variable

-element Constructs

  Tag              Caption
  Group            Initials,LastName
  Parent/Child     MedlineCitation/PMID
  Recursive        "**/Gene-commentary_accession"
  Unrestricted     "PubDate/*"
  Attribute        DescriptorName@MajorTopicYN
  Range            MedlineDate[1:4]
  Substring        "Title[phospholipase | rattlesnake]"
  Object Count     "#Author"
  Item Length      "%Title"
  Element Depth    "^PMID"
  Variable         "&NAME"

Special -element Operations

  Parent Index     "+"
  Object Name      "?"
  XML Subtree      "*"
  Children         "$"
  Attributes       "@"

Numeric Processing

  -num             Count
  -len             Length
  -sum             Sum
  -min             Minimum
  -max             Maximum
  -inc             Increment
  -dec             Decrement
  -sub             Difference
  -avg             Average
  -dev             Deviation
  -med             Median
  -mul             Product
  -div             Quotient
  -mod             Remainder
  -bin             Binary
  -bit             Bit Count

String Processing

  -encode          URL-encode <, >, &, ", and ' characters
  -decode          Base64 decoding
  -plain           Remove embedded mixed-content markup tags
  -upper           Convert text to upper-case
  -lower           Convert text to lower-case
  -chain           Change_spaces_to_underscores
  -title           Capitalize initial letters of words
  -order           Rearrange words in sorted order
  -year            Extract first 4-digit year from string
  -translate       Substitute values with -transform table

Text Processing

  -terms           Partition text at spaces
  -words           Split at punctuation marks
  -pairs           Adjacent informative words
  -reverse         Reverse words in string
  -letters         Separate individual letters
  -clauses         Break at phrase separators

Sequence Processing

  -revcomp         Reverse-complement nucleotide sequence
  -nucleic         Subrange determines forward or revcomp
  -fasta           Split sequence into blocks of 50 letters
  -molwt           Calculate molecular weight of peptide

Sequence Coordinates

  -0-based         Zero-Based
  -1-based         One-Based
  -ucsc-based      Half-Open

Command Generator

  -insd            Generate INSDSeq extraction commands

-insd Argument Order

  Descriptors      INSDSeq_sequence INSDSeq_definition INSDSeq_division
  Flags            [complete|partial]
  Feature(s)       CDS,mRNA
  Qualifiers       INSDFeature_key "#INSDInterval" gene product sub_sequence

Frequency Table

  -histogram       Collects data for sort-uniq-count on entire set of records

Entrez Indexing

  -e2index         Create Entrez index XML
  -indices         Index normalized words

Miscellaneous

  -head            Print before everything else
  -tail            Print after everything else
  -hd              Print before each record
  -tl              Print after each record

Reformatting

  -format          [copy|compact|flush|indent|expand]
                     [-unicode fuse|space|period|brackets|markdown|slash|tag]
                     [-script brackets|markdown]
                     [-mathml terse]

Modification

  -filter          Object
                     [retain|remove|encode|decode|shrink|expand|accent]
                       [content|cdata|comment|object|attributes|container]

Efetch Normalization

  -normalize      [database]

Validation

  -verify          Report XML data integrity problems

Summary

  -outline         Display outline of XML structure
  -synopsis        Display individual XML paths
  -contour         Display XML paths to leaf nodes
                     [delimiter]

Record Selection

  -select          Select record subset by conditions
  -in              File of identifiers to use for selection

Record Rearrangement

  -sort            Element to use as sort key

Data Conversion

  -j2x             Convert JSON stream to XML suitable for -path navigation
                     [-set setWrapper]
                     [-rec recordWrapper]
                     [-nest flat|recurse|plural|depth]

  -t2x             Convert tab-delimited table to XML
                     [-set setWrapper]
                     [-rec recordWrapper]
                     [-skip linesToSkip]
                     [-lower | -upper]
                     [-indent | -flush]
                     XML object names per column

  -c2x             Convert CSV (comma-separated values) file to XML
                     [-set setWrapper]
                     [-rec recordWrapper]
                     [-skip linesToSkip]
                     [-lower | -upper]
                     [-indent | -flush]
                     XML object names per column

  -g2x             Convert GenBank flatfile format to INSDSeq XML

Documentation

  -help            Print this document
  -examples        Examples of EDirect and xtract usage
  -version         Print version number

Notes

  String constraints use case-insensitive comparisons.

  Numeric constraints and selection arguments use integer values.

  -num and -len selections are synonyms for Object Count (#) and Item Length (%).

  -words, -pairs, -reverse, and -indices convert to lower case.

Examples

  -pattern DocumentSummary -element Id -first Name Title

  -pattern "PubmedArticleSet/*" -block Author -sep " " -element Initials,LastName

  -pattern PubmedArticle -block MeshHeading -if "@MajorTopicYN" -equals Y -sep " / " -element DescriptorName,QualifierName

  -pattern GenomicInfoType -element ChrAccVer ChrStart ChrStop

  -pattern Taxon -block "*/Taxon" -unless Rank -equals "no rank" -tab "\n" -element Rank,ScientificName

  -pattern Entrezgene -block "**/Gene-commentary"

  -block INSDReference -position 2

  -subset INSDInterval -position last -POS INSDInterval_to -element "&SEQ[&POS+1:]"

  -if Author -and Title

  -if "#Author" -lt 6 -and "%Title" -le 70

  -if DateRevised/Year -gt 2005

  -if ChrStop -lt ChrStart

  -if CommonName -contains mouse

  -if "&ABST" -starts-with "Transposable elements"

  -if MapLocation -element MapLocation -else -lbl "\-"

  -if inserted_sequence -differs-from deleted_sequence

  -min ChrStart,ChrStop

  -max ExonCount

  -inc position -element inserted_sequence

  -1-based ChrStart

  -insd CDS gene product protein_id translation

  -insd complete mat_peptide "%peptide" product peptide

  -insd CDS INSDInterval_iscomp@value INSDInterval_from INSDInterval_to

  -pattern PubmedArticle -select PubDate/Year -eq 2015

  -pattern PubmedArticle -select MedlineCitation/PMID -in file_of_pmids.txt

  -wrp PubmedArticleSet -pattern PubmedArticle -sort MedlineCitation/PMID

  -pattern PubmedArticle -split 5000 -prefix "subset" -suffix "xml"

  -head "<PubmedArticleSet>" -tail "</PubmedArticleSet>" -pattern PubmedArticle -format

  -pattern PubmedBookArticle -path BookDocument.Book.AuthorList.Author -element LastName

  -pattern PubmedArticle -group MedlineCitation/Article/Journal/JournalIssue/PubDate -year "PubDate/*"

  -filter ExpXml decode content

  -filter LocationHist remove object

  -mixed -verify MedlineCitation/PMID -html
`

const xtractInternal = `
StreamBlocks -> SplitPattern => StreamTokens => ParseXML => ProcessQuery -> MergeResults

Performance Default Overrides

  -proc     Number of CPU processors used
  -cons     Ratio of parsers to processors
  -serv     Concurrent parser instances
  -chan     Communication channel depth
  -heap     Order restoration heap size
  -farm     Node allocation buffer length
  -gogc     Garbage collection tuning knob

Internal Component Performance

  -chunk    StreamBlocks
  -split    StreamBlocks -> SplitPattern
  -token    StreamBlocks -> StreamTokens

Debugging

  -debug    Display run-time parameter summary
  -empty    Flag records with no output
  -ident    Print record index numbers
  -stats    Show processing time for each record
  -timer    Report processing duration and rate
  -trial    Optimize -proc value, requires -input

Documentation

  -keys     Keyboard navigation shortcuts
  -unix     Common Unix commands

Performance Tuning Script

  XtractTrials() {
    echo -e "<Trials>"
    for tries in {1..5}
    do
      xtract -debug -input "$1" -proc "$2" -pattern PubmedArticle -element LastName
    done
    echo -e "</Trials>"
  }

  for proc in {1..8}
  do
    XtractTrials "carotene.xml" "$proc" |
    xtract -pattern Trials -lbl "$proc" -avg Rate -dev Rate
  done

Processor Titration Results

  1    27622    31
  2    51799    312
  3    74853    593
  4    95867    1337
  5    97171    4019
  6    93460    2458
  7    87467    1030
  8    82448    2651

Entrez Index Performance Measurement

  IndexTrials() {
    echo -e "<Trials>"
    for tries in {1..5}
    do
      cat "$1" | xtract -debug -proc "$2" -e2index
    done
    echo -e "</Trials>"
  }

  for proc in {1..8}
  do
    IndexTrials "carotene.xml" "$proc" |
    xtract -pattern Trials -lbl "$proc" -avg Rate -dev Rate
  done

MeSH Tree Index Preparation

  ftp-cp nlmpubs.nlm.nih.gov online/mesh/MESH_FILES/xmlmesh desc2020.zip
  unzip desc2020.zip
  rm desc2020.zip

  cat desc2020.xml |
  xtract -pattern DescriptorRecord -element "DescriptorRecord/DescriptorUI" \
    -sep "," -element TreeNumber > meshtree.txt

Execution Profiling

  cat carotene.xml > /dev/null
  ./xtract -profile -timer -input carotene.xml -pattern PubmedArticle -element LastName > /dev/null
  go tool pprof --pdf ./cpu.pprof > ~/Desktop/callgraph.pdf
  rm cpu.pprof
`

const keyboardShortcuts = `
Command History

  Ctrl-n     Next command
  Ctrl-p     Previous command

Move Cursor Forward

  Ctrl-e     To end of line
  Ctrl-f     By one character
  Esc-f      By one argument

Move Cursor Backward

  Ctrl-a     To beginning of line
  Ctrl-b     By one character
  Esc-b      By one argument

Delete

  Del        Previous character
  Ctrl-d     Next character
  Ctrl-k     To end of line
  Ctrl-u     Entire line
  Ctrl-w     Previous word
  Esc-Del    Previous argument
  Esc-d      Next argument

Autocomplete

  Tab        Completes directory or file names

Program Control

  Ctrl-c     Quit running program
  ^x^y       Run last command replacing x with y
  Ctrl-z     Suspend foreground job
  kill %%    Quit suspended script
`

const unixCommands = `
Process by Contents

 sort      Sorts lines of text

  -f       Ignore case
  -n       Numeric comparison
  -r       Reverse result order

  -k       Field key (start,stop or first)
  -u       Unique lines with identical keys

  -b       Ignore leading blanks
  -s       Stable sort
  -t       Specify field separator

 uniq      Removes repeated lines

  -c       Count occurrences
  -i       Ignore case

  -f       Ignore first n fields
  -s       Ignore first n characters

  -d       Only output repeated lines
  -u       Only output non-repeated lines

 grep      Matches patterns using regular expressions

  -i       Ignore case
  -v       Invert search
  -w       Search expression as a word
  -x       Search expression as whole line

  -e       Specify individual pattern

  -c       Only count number of matches
  -n       Print line numbers
  -A       Number of lines after match
  -B       Number of lines before match

Regular Expressions

 Characters

  .        Any single character (except newline)
  \w       Alphabetic [A-Za-z], numeric [0-9], or underscore (_)
  \s       Whitespace (space or tab)
  \        Escapes special characters
  []       Matches any enclosed characters

 Positions

  ^        Beginning of line
  $        End of line
  \b       Word boundary

 Repeat Matches

  ?        0 or 1
  *        0 or more
  +        1 or more
  {n}      Exactly n

 Escape Sequences

  \n       Line break
  \t       Tab character

Modify Contents

 sed       Replaces text strings

  -e       Specify individual expression
  s///     Substitute
     /g    Global
     /I    Case-insensitive
     /p    Print

 tr        Translates characters

  -d       Delete character
  -s       Squeeze runs of characters

 rev       Reverses characters on line

Format Contents

 column    Aligns columns by content width

  -s       Specify field separator
  -t       Create table

 expand    Aligns columns to specified positions

  -t       Tab positions

 fold      Wraps lines at a specific width

  -w       Line width
  -s       Fold at spaces

Filter by Position

 cut       Removes parts of lines

  -c       Characters to keep
  -f       Fields to keep
  -d       Specify field separator
  -s       Suppress lines with no delimiters

 head      Prints first lines

  -n       Number of lines

 tail      Prints last lines

  -n       Number of lines

Miscellaneous

 wc        Counts words, lines, or characters

  -c       Characters
  -l       Lines
  -w       Words

 xargs     Constructs arguments

  -n       Number of words per batch

 mktemp    Make temporary file

File Compression

 tar       Archive files

  -c       Create archive
  -f       Name of output file
  -z       Compress archive with gzip

 gzip      Compress file

  -k       Keep original file
  -9       Best compression

 unzip     Decompress .zip archive

  -p       Pipe to stdout

 gzcat     Decompress .gz archive and pipe to stdout

Directory and File Navigation

 cd        Changes directory

  /        Root
  ~        Home
  .        Current
  ..       Parent
  -        Previous

 ls        Lists file names

  -1       One entry per line
  -a       Show files beginning with dot (.)
  -l       List in long format
  -R       Recursively explore subdirectories
  -S       Sort files by size
  -t       Sort by most recently modified
  .*       Current and parent directory

 pwd       Prints working directory path

File Redirection

  <        Read stdin from file
  >        Redirect stdout to file
  >>       Append to file
  2>       Redirect stderr
  2>&1     Merge stderr into stdout
  |        Pipe between programs
  <(cmd)   Execute command, read results as file

Shell Script Variables

  $0       Name of script
  $n       Nth argument
  $#       Number of arguments
  "$*"     Argument list as one argument
  "$@"     Argument list as separate arguments
  $?       Exit status of previous command

Shell Script Tests

  -d       Directory exists
  -f       File exists
  -s       File is not empty
  -n       Length of string is non-zero
  -x       File is executable
  -z       Variable is empty or not set

File and Directory Extraction

           BAS=$(printf pubmed%03d $n)
           DIR=$(dirname "$0")
           FIL=$(basename "$0")

Remove Prefix

           FILE="example.tar.gz"
  #        ${FILE#.*}  -> tar.gz
  ##       ${FILE##.*} -> gz

Remove Suffix

           FILE="example.tar.gz"
           TYPE="http://identifiers.org/uniprot_enzymes/"
  %        ${FILE%.*}  -> example.tar
           ${TYPE%/}   -> http://identifiers.org/uniprot_enzymes
  %%       ${FILE%%.*} -> example
`

// TYPED CONSTANTS

type LevelType int

const (
	_ LevelType = iota
	UNIT
	SUBSET
	SECTION
	BLOCK
	BRANCH
	GROUP
	DIVISION
	PATH
	PATTERN
)

type IndentType int

const (
	SINGULARITY IndentType = iota
	COMPACT
	FLUSH
	INDENT
	SUBTREE
	WRAPPED
)

type OpType int

const (
	UNSET OpType = iota
	ELEMENT
	FIRST
	LAST
	ENCODE
	DECODE
	PLAIN
	UPPER
	LOWER
	CHAIN
	TITLE
	ORDER
	YEAR
	TRANSLATE
	TERMS
	WORDS
	PAIRS
	REVERSE
	LETTERS
	CLAUSES
	INDICES
	MESHCODE
	MATRIX
	HISTOGRAM
	ACCENTED
	PFX
	SFX
	SEP
	TAB
	RET
	LBL
	CLR
	PFC
	DEQ
	PLG
	ELG
	FWD
	AWD
	WRP
	RST
	DEF
	COLOR
	POSITION
	SELECT
	IF
	UNLESS
	MATCH
	AVOID
	AND
	OR
	EQUALS
	CONTAINS
	ISWITHIN
	STARTSWITH
	ENDSWITH
	ISNOT
	ISBEFORE
	ISAFTER
	MATCHES
	RESEMBLES
	ISEQUALTO
	DIFFERSFROM
	GT
	GE
	LT
	LE
	EQ
	NE
	NUM
	LEN
	SUM
	MIN
	MAX
	INC
	DEC
	SUB
	AVG
	DEV
	MED
	MUL
	DIV
	MOD
	BIN
	BIT
	ZEROBASED
	ONEBASED
	UCSCBASED
	REVCOMP
	NUCLEIC
	FASTA
	MOLWT
	ELSE
	VARIABLE
	VALUE
	QUESTION
	STAR
	DOLLAR
	ATSIGN
	COUNT
	LENGTH
	DEPTH
	INDEX
	UNRECOGNIZED
)

type ArgumentType int

const (
	_ ArgumentType = iota
	EXPLORATION
	CONDITIONAL
	EXTRACTION
	CUSTOMIZATION
)

type RangeType int

const (
	NORANGE RangeType = iota
	STRINGRANGE
	VARIABLERANGE
	INTEGERRANGE
)

type SeqEndType int

const (
	_ SeqEndType = iota
	ISSTART
	ISSTOP
	ISPOS
)

type SequenceType struct {
	Based int
	Which SeqEndType
}

// MUTEXES

var hlock sync.Mutex

var slock sync.RWMutex

// ARGUMENT MAPS

var argTypeIs = map[string]ArgumentType{
	"-unit":         EXPLORATION,
	"-Unit":         EXPLORATION,
	"-subset":       EXPLORATION,
	"-Subset":       EXPLORATION,
	"-section":      EXPLORATION,
	"-Section":      EXPLORATION,
	"-block":        EXPLORATION,
	"-Block":        EXPLORATION,
	"-branch":       EXPLORATION,
	"-Branch":       EXPLORATION,
	"-group":        EXPLORATION,
	"-Group":        EXPLORATION,
	"-division":     EXPLORATION,
	"-Division":     EXPLORATION,
	"-path":         EXPLORATION,
	"-Path":         EXPLORATION,
	"-pattern":      EXPLORATION,
	"-Pattern":      EXPLORATION,
	"-position":     CONDITIONAL,
	"-select":       CONDITIONAL,
	"-if":           CONDITIONAL,
	"-unless":       CONDITIONAL,
	"-match":        CONDITIONAL,
	"-avoid":        CONDITIONAL,
	"-and":          CONDITIONAL,
	"-or":           CONDITIONAL,
	"-equals":       CONDITIONAL,
	"-contains":     CONDITIONAL,
	"-is-within":    CONDITIONAL,
	"-starts-with":  CONDITIONAL,
	"-ends-with":    CONDITIONAL,
	"-is-not":       CONDITIONAL,
	"-is-before":    CONDITIONAL,
	"-is-after":     CONDITIONAL,
	"-matches":      CONDITIONAL,
	"-resembles":    CONDITIONAL,
	"-is-equal-to":  CONDITIONAL,
	"-differs-from": CONDITIONAL,
	"-gt":           CONDITIONAL,
	"-ge":           CONDITIONAL,
	"-lt":           CONDITIONAL,
	"-le":           CONDITIONAL,
	"-eq":           CONDITIONAL,
	"-ne":           CONDITIONAL,
	"-element":      EXTRACTION,
	"-first":        EXTRACTION,
	"-last":         EXTRACTION,
	"-encode":       EXTRACTION,
	"-decode":       EXTRACTION,
	"-plain":        EXTRACTION,
	"-upper":        EXTRACTION,
	"-lower":        EXTRACTION,
	"-chain":        EXTRACTION,
	"-title":        EXTRACTION,
	"-order":        EXTRACTION,
	"-year":         EXTRACTION,
	"-translate":    EXTRACTION,
	"-terms":        EXTRACTION,
	"-words":        EXTRACTION,
	"-pairs":        EXTRACTION,
	"-reverse":      EXTRACTION,
	"-letters":      EXTRACTION,
	"-clauses":      EXTRACTION,
	"-indices":      EXTRACTION,
	"-meshcode":     EXTRACTION,
	"-matrix":       EXTRACTION,
	"-histogram":    EXTRACTION,
	"-accented":     EXTRACTION,
	"-num":          EXTRACTION,
	"-len":          EXTRACTION,
	"-sum":          EXTRACTION,
	"-min":          EXTRACTION,
	"-max":          EXTRACTION,
	"-inc":          EXTRACTION,
	"-dec":          EXTRACTION,
	"-sub":          EXTRACTION,
	"-avg":          EXTRACTION,
	"-dev":          EXTRACTION,
	"-med":          EXTRACTION,
	"-mul":          EXTRACTION,
	"-div":          EXTRACTION,
	"-mod":          EXTRACTION,
	"-bin":          EXTRACTION,
	"-bit":          EXTRACTION,
	"-0-based":      EXTRACTION,
	"-zero-based":   EXTRACTION,
	"-1-based":      EXTRACTION,
	"-one-based":    EXTRACTION,
	"-ucsc":         EXTRACTION,
	"-ucsc-based":   EXTRACTION,
	"-ucsc-coords":  EXTRACTION,
	"-bed-based":    EXTRACTION,
	"-bed-coords":   EXTRACTION,
	"-revcomp":      EXTRACTION,
	"-nucleic":      EXTRACTION,
	"-fasta":        EXTRACTION,
	"-molwt":        EXTRACTION,
	"-else":         EXTRACTION,
	"-pfx":          CUSTOMIZATION,
	"-sfx":          CUSTOMIZATION,
	"-sep":          CUSTOMIZATION,
	"-tab":          CUSTOMIZATION,
	"-ret":          CUSTOMIZATION,
	"-lbl":          CUSTOMIZATION,
	"-clr":          CUSTOMIZATION,
	"-pfc":          CUSTOMIZATION,
	"-deq":          CUSTOMIZATION,
	"-plg":          CUSTOMIZATION,
	"-elg":          CUSTOMIZATION,
	"-fwd":          CUSTOMIZATION,
	"-awd":          CUSTOMIZATION,
	"-wrp":          CUSTOMIZATION,
	"-rst":          CUSTOMIZATION,
	"-def":          CUSTOMIZATION,
	"-color":        CUSTOMIZATION,
}

var opTypeIs = map[string]OpType{
	"-element":      ELEMENT,
	"-first":        FIRST,
	"-last":         LAST,
	"-encode":       ENCODE,
	"-decode":       DECODE,
	"-plain":        PLAIN,
	"-upper":        UPPER,
	"-lower":        LOWER,
	"-chain":        CHAIN,
	"-title":        TITLE,
	"-order":        ORDER,
	"-year":         YEAR,
	"-translate":    TRANSLATE,
	"-terms":        TERMS,
	"-words":        WORDS,
	"-pairs":        PAIRS,
	"-reverse":      REVERSE,
	"-letters":      LETTERS,
	"-clauses":      CLAUSES,
	"-indices":      INDICES,
	"-meshcode":     MESHCODE,
	"-matrix":       MATRIX,
	"-histogram":    HISTOGRAM,
	"-accented":     ACCENTED,
	"-pfx":          PFX,
	"-sfx":          SFX,
	"-sep":          SEP,
	"-tab":          TAB,
	"-ret":          RET,
	"-lbl":          LBL,
	"-clr":          CLR,
	"-pfc":          PFC,
	"-deq":          DEQ,
	"-plg":          PLG,
	"-elg":          ELG,
	"-fwd":          FWD,
	"-awd":          AWD,
	"-wrp":          WRP,
	"-rst":          RST,
	"-def":          DEF,
	"-color":        COLOR,
	"-position":     POSITION,
	"-select":       SELECT,
	"-if":           IF,
	"-unless":       UNLESS,
	"-match":        MATCH,
	"-avoid":        AVOID,
	"-and":          AND,
	"-or":           OR,
	"-equals":       EQUALS,
	"-contains":     CONTAINS,
	"-is-within":    ISWITHIN,
	"-starts-with":  STARTSWITH,
	"-ends-with":    ENDSWITH,
	"-is-not":       ISNOT,
	"-is-before":    ISBEFORE,
	"-is-after":     ISAFTER,
	"-matches":      MATCHES,
	"-resembles":    RESEMBLES,
	"-is-equal-to":  ISEQUALTO,
	"-differs-from": DIFFERSFROM,
	"-gt":           GT,
	"-ge":           GE,
	"-lt":           LT,
	"-le":           LE,
	"-eq":           EQ,
	"-ne":           NE,
	"-num":          NUM,
	"-len":          LEN,
	"-sum":          SUM,
	"-min":          MIN,
	"-max":          MAX,
	"-inc":          INC,
	"-dec":          DEC,
	"-sub":          SUB,
	"-avg":          AVG,
	"-dev":          DEV,
	"-med":          MED,
	"-mul":          MUL,
	"-div":          DIV,
	"-mod":          MOD,
	"-bin":          BIN,
	"-bit":          BIT,
	"-0-based":      ZEROBASED,
	"-zero-based":   ZEROBASED,
	"-1-based":      ONEBASED,
	"-one-based":    ONEBASED,
	"-ucsc":         UCSCBASED,
	"-ucsc-based":   UCSCBASED,
	"-ucsc-coords":  UCSCBASED,
	"-bed-based":    UCSCBASED,
	"-bed-coords":   UCSCBASED,
	"-revcomp":      REVCOMP,
	"-nucleic":      NUCLEIC,
	"-fasta":        FASTA,
	"-molwt":        MOLWT,
	"-else":         ELSE,
}

var sequenceTypeIs = map[string]SequenceType{
	"INSDSeq:INSDInterval_from":       {1, ISSTART},
	"INSDSeq:INSDInterval_to":         {1, ISSTOP},
	"DocumentSummary:ChrStart":        {0, ISSTART},
	"DocumentSummary:ChrStop":         {0, ISSTOP},
	"DocumentSummary:Chr_start":       {1, ISSTART},
	"DocumentSummary:Chr_end":         {1, ISSTOP},
	"DocumentSummary:Chr_inner_start": {1, ISSTART},
	"DocumentSummary:Chr_inner_end":   {1, ISSTOP},
	"DocumentSummary:Chr_outer_start": {1, ISSTART},
	"DocumentSummary:Chr_outer_end":   {1, ISSTOP},
	"DocumentSummary:start":           {1, ISSTART},
	"DocumentSummary:stop":            {1, ISSTOP},
	"DocumentSummary:display_start":   {1, ISSTART},
	"DocumentSummary:display_stop":    {1, ISSTOP},
	"Entrezgene:Seq-interval_from":    {0, ISSTART},
	"Entrezgene:Seq-interval_to":      {0, ISSTOP},
	"GenomicInfoType:ChrStart":        {0, ISSTART},
	"GenomicInfoType:ChrStop":         {0, ISSTOP},
	"RS:position":                     {0, ISPOS},
	"RS:@asnFrom":                     {0, ISSTART},
	"RS:@asnTo":                       {0, ISSTOP},
	"RS:@end":                         {0, ISSTOP},
	"RS:@leftContigNeighborPos":       {0, ISSTART},
	"RS:@physMapInt":                  {0, ISPOS},
	"RS:@protLoc":                     {0, ISPOS},
	"RS:@rightContigNeighborPos":      {0, ISSTOP},
	"RS:@start":                       {0, ISSTART},
	"RS:@structLoc":                   {0, ISPOS},
}

var revComp = map[rune]rune{
	'A': 'T',
	'B': 'V',
	'C': 'G',
	'D': 'H',
	'G': 'C',
	'H': 'D',
	'K': 'M',
	'M': 'K',
	'N': 'N',
	'R': 'Y',
	'S': 'S',
	'T': 'A',
	'U': 'A',
	'V': 'B',
	'W': 'W',
	'X': 'X',
	'Y': 'R',
	'a': 't',
	'b': 'v',
	'c': 'g',
	'd': 'h',
	'g': 'c',
	'h': 'd',
	'k': 'm',
	'm': 'k',
	'n': 'n',
	'r': 'y',
	's': 's',
	't': 'a',
	'u': 'a',
	'v': 'b',
	'w': 'w',
	'x': 'x',
	'y': 'r',
}

var numC = map[rune]int{
	'A': 3,
	'B': 4,
	'C': 3,
	'D': 4,
	'E': 5,
	'F': 9,
	'G': 2,
	'H': 6,
	'I': 6,
	'J': 6,
	'K': 6,
	'L': 6,
	'M': 5,
	'N': 4,
	'O': 12,
	'P': 5,
	'Q': 5,
	'R': 6,
	'S': 3,
	'T': 4,
	'U': 3,
	'V': 5,
	'W': 11,
	'X': 0,
	'Y': 9,
	'Z': 5,
}

var numH = map[rune]int{
	'A': 5,
	'B': 5,
	'C': 5,
	'D': 5,
	'E': 7,
	'F': 9,
	'G': 3,
	'H': 7,
	'I': 11,
	'J': 11,
	'K': 12,
	'L': 11,
	'M': 9,
	'N': 6,
	'O': 19,
	'P': 7,
	'Q': 8,
	'R': 12,
	'S': 5,
	'T': 7,
	'U': 5,
	'V': 9,
	'W': 10,
	'X': 0,
	'Y': 9,
	'Z': 7,
}

var numN = map[rune]int{
	'A': 1,
	'B': 1,
	'C': 1,
	'D': 1,
	'E': 1,
	'F': 1,
	'G': 1,
	'H': 3,
	'I': 1,
	'J': 1,
	'K': 2,
	'L': 1,
	'M': 1,
	'N': 2,
	'O': 3,
	'P': 1,
	'Q': 2,
	'R': 4,
	'S': 1,
	'T': 1,
	'U': 1,
	'V': 1,
	'W': 2,
	'X': 0,
	'Y': 1,
	'Z': 1,
}

var numO = map[rune]int{
	'A': 1,
	'B': 3,
	'C': 1,
	'D': 3,
	'E': 3,
	'F': 1,
	'G': 1,
	'H': 1,
	'I': 1,
	'J': 1,
	'K': 1,
	'L': 1,
	'M': 1,
	'N': 2,
	'O': 2,
	'P': 1,
	'Q': 2,
	'R': 1,
	'S': 2,
	'T': 2,
	'U': 1,
	'V': 1,
	'W': 1,
	'X': 0,
	'Y': 2,
	'Z': 3,
}

var numS = map[rune]int{
	'A': 0,
	'B': 0,
	'C': 1,
	'D': 0,
	'E': 0,
	'F': 0,
	'G': 0,
	'H': 0,
	'I': 0,
	'J': 0,
	'K': 0,
	'L': 0,
	'M': 1,
	'N': 0,
	'O': 0,
	'P': 0,
	'Q': 0,
	'R': 0,
	'S': 0,
	'T': 0,
	'U': 0,
	'V': 0,
	'W': 0,
	'X': 0,
	'Y': 0,
	'Z': 0,
}

var numSe = map[rune]int{
	'A': 0,
	'B': 0,
	'C': 0,
	'D': 0,
	'E': 0,
	'F': 0,
	'G': 0,
	'H': 0,
	'I': 0,
	'J': 0,
	'K': 0,
	'L': 0,
	'M': 0,
	'N': 0,
	'O': 0,
	'P': 0,
	'Q': 0,
	'R': 0,
	'S': 0,
	'T': 0,
	'U': 1,
	'V': 0,
	'W': 0,
	'X': 0,
	'Y': 0,
	'Z': 0,
}

// DATA OBJECTS

type Step struct {
	Type   OpType
	Value  string
	Parent string
	Match  string
	Attrib string
	TypL   RangeType
	StrL   string
	IntL   int
	TypR   RangeType
	StrR   string
	IntR   int
	Norm   bool
	Wild   bool
}

type Operation struct {
	Type   OpType
	Value  string
	Stages []*Step
}

type Block struct {
	Visit      string
	Parent     string
	Match      string
	Path       []string
	Working    []string
	Parsed     []string
	Position   string
	Foreword   string
	Afterword  string
	Conditions []*Operation
	Commands   []*Operation
	Failure    []*Operation
	Subtasks   []*Block
}

type Limiter struct {
	Obj *Node
	Idx int
	Lvl int
}

// UTILITIES

func ParseFlag(str string) OpType {

	op, ok := opTypeIs[str]
	if ok {
		return op
	}

	if len(str) > 1 && str[0] == '-' && IsAllCapsOrDigits(str[1:]) {
		return VARIABLE
	}

	if len(str) > 0 && str[0] == '-' {
		return UNRECOGNIZED
	}

	return UNSET
}

func ParseMarkup(str, cmd string) MarkupPolicy {

	switch str {
	case "fuse", "fused":
		return FUSE
	case "space", "spaces":
		return SPACE
	case "period", "periods":
		return PERIOD
	case "bracket", "brackets":
		return BRACKETS
	case "markdown":
		return MARKDOWN
	case "slash":
		return SLASH
	case "tag", "tags":
		return TAGS
	case "terse":
		return TERSE
	default:
		if str != "" {
			fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized %s value '%s'\n", cmd, str)
			os.Exit(1)
		}
	}
	return NOMARKUP
}

// DebugBlock examines structure of parsed arguments (undocumented)
/*
func DebugBlock(blk *Block, depth int) {

	doIndent := func(indt int) {
		for i := 1; i < indt; i++ {
			fmt.Fprintf(os.Stderr, "  ")
		}
	}

	doIndent(depth)

	if blk.Visit != "" {
		doIndent(depth + 1)
		fmt.Fprintf(os.Stderr, "<Visit> %s </Visit>\n", blk.Visit)
	}
	if len(blk.Parsed) > 0 {
		doIndent(depth + 1)
		fmt.Fprintf(os.Stderr, "<Parsed>")
		for _, str := range blk.Parsed {
			fmt.Fprintf(os.Stderr, " %s", str)
		}
		fmt.Fprintf(os.Stderr, " </Parsed>\n")
	}

	if len(blk.Subtasks) > 0 {
		for _, sub := range blk.Subtasks {
			DebugBlock(sub, depth+1)
		}
	}
}
*/

// PARSE COMMAND-LINE ARGUMENTS

// ParseArguments parses nested exploration instruction from command-line arguments
func ParseArguments(cmdargs []string, pttrn string) *Block {

	// different names of exploration control arguments allow multiple levels of nested "for" loops in a linear command line
	// (capitalized versions for backward-compatibility with original Perl implementation handling of recursive definitions)
	var (
		lcname = []string{
			"",
			"-unit",
			"-subset",
			"-section",
			"-block",
			"-branch",
			"-group",
			"-division",
			"-path",
			"-pattern",
		}

		ucname = []string{
			"",
			"-Unit",
			"-Subset",
			"-Section",
			"-Block",
			"-Branch",
			"-Group",
			"-Division",
			"-Path",
			"-Pattern",
		}
	)

	// parseCommands recursive definition
	var parseCommands func(parent *Block, startLevel LevelType)

	// parseCommands does initial parsing of exploration command structure
	parseCommands = func(parent *Block, startLevel LevelType) {

		// find next highest level exploration argument
		findNextLevel := func(args []string, level LevelType) (LevelType, string, string) {

			if len(args) > 1 {

				for {

					if level < UNIT {
						break
					}

					lctag := lcname[level]
					uctag := ucname[level]

					for _, txt := range args {
						if txt == lctag || txt == uctag {
							return level, lctag, uctag
						}
					}

					level--
				}
			}

			return 0, "", ""
		}

		arguments := parent.Working

		level, lctag, uctag := findNextLevel(arguments, startLevel)

		if level < UNIT {

			// break recursion
			return
		}

		// group arguments at a given exploration level
		subsetCommands := func(args []string) *Block {

			max := len(args)

			visit := ""

			// extract name of object to visit
			if max > 1 {
				visit = args[1]
				args = args[2:]
				max -= 2
			}

			partition := 0
			for cur, str := range args {

				// record point of next exploration command
				partition = cur + 1

				// skip if not a command
				if len(str) < 1 || str[0] != '-' {
					continue
				}

				if argTypeIs[str] == EXPLORATION {
					partition = cur
					break
				}
			}

			// convert slashes (e.g., parent/child construct) to periods (e.g., dotted exploration path)
			if strings.Contains(visit, "/") {
				if !strings.Contains(visit, ".") {
					visit = strings.Replace(visit, "/", ".", -1)
				}
			}

			// parse parent.child or dotted path construct
			// colon indicates a namespace prefix in any or all of the components
			prnt, rmdr := SplitInTwoAt(visit, ".", RIGHT)
			match, rest := SplitInTwoAt(rmdr, ".", LEFT)

			if rest != "" {

				// exploration match on first component, then search remainder one level at a time with subsequent components
				dirs := strings.Split(rmdr, ".")

				// signal with "path" position
				return &Block{Visit: visit, Parent: "", Match: prnt, Path: dirs, Position: "path", Parsed: args[0:partition], Working: args[partition:]}
			}

			// promote arguments parsed at this level
			return &Block{Visit: visit, Parent: prnt, Match: match, Parsed: args[0:partition], Working: args[partition:]}
		}

		cur := 0

		// search for positions of current exploration command

		for idx, txt := range arguments {
			if txt == lctag || txt == uctag {
				if idx == 0 {
					continue
				}

				blk := subsetCommands(arguments[cur:idx])
				parseCommands(blk, level-1)
				parent.Subtasks = append(parent.Subtasks, blk)

				cur = idx
			}
		}

		if cur < len(arguments) {
			blk := subsetCommands(arguments[cur:])
			parseCommands(blk, level-1)
			parent.Subtasks = append(parent.Subtasks, blk)
		}

		// clear execution arguments from parent after subsetting
		parent.Working = nil
	}

	// parse optional [min:max], [&VAR:&VAR], or [after|before] range specification
	parseRange := func(item, rnge string) (typL RangeType, strL string, intL int, typR RangeType, strR string, intR int) {

		typL = NORANGE
		typR = NORANGE
		strL = ""
		strR = ""
		intL = 0
		intR = 0

		if rnge == "" {
			// no range specification, return default values
			return
		}

		// check if last character is right square bracket
		if !strings.HasSuffix(rnge, "]") {
			fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized range %s\n", rnge)
			os.Exit(1)
		}

		rnge = strings.TrimSuffix(rnge, "]")

		if rnge == "" {
			fmt.Fprintf(os.Stderr, "\nERROR: Empty range %s[]\n", item)
			os.Exit(1)
		}

		// check for [after|before] variant
		if strings.Contains(rnge, "|") {

			strL, strR = SplitInTwoAt(rnge, "|", LEFT)
			// spacing matters, so do not call TrimSpace

			if strL == "" && strR == "" {
				fmt.Fprintf(os.Stderr, "\nERROR: Empty range %s[|]\n", item)
				os.Exit(1)
			}

			typL = STRINGRANGE
			typR = STRINGRANGE

			// return statement returns named variables
			return
		}

		// otherwise must have colon within brackets
		if !strings.Contains(rnge, ":") {
			fmt.Fprintf(os.Stderr, "\nERROR: Colon missing in range %s[%s]\n", item, rnge)
			os.Exit(1)
		}

		// split at colon
		lft, rgt := SplitInTwoAt(rnge, ":", LEFT)

		lft = strings.TrimSpace(lft)
		rgt = strings.TrimSpace(rgt)

		if lft == "" && rgt == "" {
			fmt.Fprintf(os.Stderr, "\nERROR: Empty range %s[:]\n", item)
			os.Exit(1)
		}

		// for variable, parse optional +/- offset suffix
		parseOffset := func(str string) (string, int) {

			if str == "" || str[0] == ' ' {
				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized variable '&%s'\n", str)
				os.Exit(1)
			}

			pls := ""
			mns := ""

			ofs := 0

			// check for &VAR+1 or &VAR-1 integer adjustment
			str, pls = SplitInTwoAt(str, "+", LEFT)
			str, mns = SplitInTwoAt(str, "-", LEFT)

			if pls != "" {
				val, err := strconv.Atoi(pls)
				if err != nil {
					fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized range adjustment &%s+%s\n", str, pls)
					os.Exit(1)
				}
				ofs = val
			} else if mns != "" {
				val, err := strconv.Atoi(mns)
				if err != nil {
					fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized range adjustment &%s-%s\n", str, mns)
					os.Exit(1)
				}
				ofs = -val
			}

			return str, ofs
		}

		// parse integer position, 1-based coordinate must be greater than 0
		parseInteger := func(str string, mustBePositive bool) int {
			if str == "" {
				return 0
			}

			val, err := strconv.Atoi(str)
			if err != nil {
				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized range component %s[%s:]\n", item, str)
				os.Exit(1)
			}
			if mustBePositive {
				if val < 1 {
					fmt.Fprintf(os.Stderr, "\nERROR: Range component %s[%s:] must be positive\n", item, str)
					os.Exit(1)
				}
			} else {
				if val == 0 {
					fmt.Fprintf(os.Stderr, "\nERROR: Range component %s[%s:] must not be zero\n", item, str)
					os.Exit(1)
				}
			}

			return val
		}

		if lft != "" {
			if lft[0] == '&' {
				lft = lft[1:]
				strL, intL = parseOffset(lft)
				typL = VARIABLERANGE
			} else {
				intL = parseInteger(lft, true)
				typL = INTEGERRANGE
			}
		}

		if rgt != "" {
			if rgt[0] == '&' {
				rgt = rgt[1:]
				strR, intR = parseOffset(rgt)
				typR = VARIABLERANGE
			} else {
				intR = parseInteger(rgt, false)
				typR = INTEGERRANGE
			}
		}

		// return statement required to return named variables
		return
	}

	parseConditionals := func(cmds *Block, arguments []string) []*Operation {

		max := len(arguments)
		if max < 1 {
			return nil
		}

		// check for missing condition command
		txt := arguments[0]
		if txt != "-if" && txt != "-unless" && txt != "-select" && txt != "-match" && txt != "-avoid" && txt != "-position" {
			fmt.Fprintf(os.Stderr, "\nERROR: Missing -if command before '%s'\n", txt)
			os.Exit(1)
		}
		if txt == "-position" && max > 2 {
			fmt.Fprintf(os.Stderr, "\nERROR: Cannot combine -position with -if or -unless commands\n")
			os.Exit(1)
		}
		// check for missing argument after last condition
		txt = arguments[max-1]
		if len(txt) > 0 && txt[0] == '-' {
			fmt.Fprintf(os.Stderr, "\nERROR: Item missing after %s command\n", txt)
			os.Exit(1)
		}

		cond := make([]*Operation, 0, max)

		// parse conditional clause into execution step
		parseStep := func(op *Operation, elementColonValue bool) {

			if op == nil {
				return
			}

			str := op.Value

			status := ELEMENT

			// isolate and parse optional [min:max], [&VAR:&VAR], or [after|before] range specification
			str, rnge := SplitInTwoAt(str, "[", LEFT)

			str = strings.TrimSpace(str)
			rnge = strings.TrimSpace(rnge)

			if str == "" && rnge != "" {
				fmt.Fprintf(os.Stderr, "\nERROR: Variable missing in range specification [%s\n", rnge)
				os.Exit(1)
			}

			typL, strL, intL, typR, strR, intR := parseRange(str, rnge)

			// check for pound, percent, or caret character at beginning of name
			if len(str) > 1 {
				switch str[0] {
				case '&':
					if IsAllCapsOrDigits(str[1:]) {
						status = VARIABLE
						str = str[1:]
					} else if strings.Contains(str, ":") {
						fmt.Fprintf(os.Stderr, "\nERROR: Unsupported construct '%s', use -if &VARIABLE -equals VALUE instead\n", str)
						os.Exit(1)
					} else {
						fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized variable '%s'\n", str)
						os.Exit(1)
					}
				case '#':
					status = COUNT
					str = str[1:]
				case '%':
					status = LENGTH
					str = str[1:]
				case '^':
					status = DEPTH
					str = str[1:]
				default:
				}
			} else if str == "+" {
				status = INDEX
			}

			// parse parent/element@attribute construct
			// colon indicates a namespace prefix in any or all of the components
			prnt, match := SplitInTwoAt(str, "/", RIGHT)
			match, attrib := SplitInTwoAt(match, "@", LEFT)
			val := ""

			// leading colon indicates namespace prefix wildcard
			wildcard := false
			if strings.HasPrefix(prnt, ":") || strings.HasPrefix(match, ":") || strings.HasPrefix(attrib, ":") {
				wildcard = true
			}

			if elementColonValue {

				// allow parent/element@attribute:value construct for deprecated -match and -avoid, and for subsequent -and and -or commands
				match, val = SplitInTwoAt(str, ":", LEFT)
				prnt, match = SplitInTwoAt(match, "/", RIGHT)
				match, attrib = SplitInTwoAt(match, "@", LEFT)
			}

			norm := true
			if rnge != "" {
				if typL != NORANGE || typR != NORANGE || strL != "" || strR != "" || intL != 0 || intR != 0 {
					norm = false
				}
			}

			tsk := &Step{Type: status, Value: str, Parent: prnt, Match: match, Attrib: attrib,
				TypL: typL, StrL: strL, IntL: intL, TypR: typR, StrR: strR, IntR: intR,
				Norm: norm, Wild: wildcard}

			op.Stages = append(op.Stages, tsk)

			// transform old -match "element:value" to -match element -equals value
			if val != "" {
				tsk := &Step{Type: EQUALS, Value: val}
				op.Stages = append(op.Stages, tsk)
			}
		}

		idx := 0

		// conditionals should alternate between command and object/value
		expectDash := true
		last := ""

		var op *Operation

		// flag to allow element-colon-value for deprecated -match and -avoid commands, otherwise colon is for namespace prefixes
		elementColonValue := false

		status := UNSET

		// parse command strings into operation structure
		for idx < max {
			str := arguments[idx]
			idx++

			// conditionals should alternate between command and object/value
			if expectDash {
				if len(str) < 1 || str[0] != '-' {
					fmt.Fprintf(os.Stderr, "\nERROR: Unexpected '%s' argument after '%s'\n", str, last)
					os.Exit(1)
				}
				expectDash = false
			} else {
				if len(str) > 0 && str[0] == '-' {
					fmt.Fprintf(os.Stderr, "\nERROR: Unexpected '%s' command after '%s'\n", str, last)
					os.Exit(1)
				}
				expectDash = true
			}
			last = str

			switch status {
			case UNSET:
				status = ParseFlag(str)
			case POSITION:
				if cmds.Position != "" {
					fmt.Fprintf(os.Stderr, "\nERROR: -position '%s' conflicts with existing '%s'\n", str, cmds.Position)
					os.Exit(1)
				}
				cmds.Position = str
				status = UNSET
			case MATCH, AVOID:
				elementColonValue = true
				fallthrough
			case SELECT, IF, UNLESS, AND, OR:
				op = &Operation{Type: status, Value: str}
				cond = append(cond, op)
				parseStep(op, elementColonValue)
				status = UNSET
			case EQUALS, CONTAINS, ISWITHIN, STARTSWITH, ENDSWITH, ISNOT, ISBEFORE, ISAFTER:
				if op != nil {
					if len(str) > 1 && str[0] == '\\' {
						// first character may be backslash protecting dash (undocumented)
						str = str[1:]
					}
					tsk := &Step{Type: status, Value: str}
					op.Stages = append(op.Stages, tsk)
					op = nil
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unexpected adjacent string match constraints\n")
					os.Exit(1)
				}
				status = UNSET
			case MATCHES:
				if op != nil {
					if len(str) > 1 && str[0] == '\\' {
						// first character may be backslash protecting dash (undocumented)
						str = str[1:]
					}
					str = RemoveCommaOrSemicolon(str)
					tsk := &Step{Type: status, Value: str}
					op.Stages = append(op.Stages, tsk)
					op = nil
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unexpected adjacent string match constraints\n")
					os.Exit(1)
				}
				status = UNSET
			case RESEMBLES:
				if op != nil {
					if len(str) > 1 && str[0] == '\\' {
						// first character may be backslash protecting dash (undocumented)
						str = str[1:]
					}
					str = SortStringByWords(str)
					tsk := &Step{Type: status, Value: str}
					op.Stages = append(op.Stages, tsk)
					op = nil
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unexpected adjacent string match constraints\n")
					os.Exit(1)
				}
				status = UNSET
			case ISEQUALTO, DIFFERSFROM:
				if op != nil {
					if len(str) < 1 {
						fmt.Fprintf(os.Stderr, "\nERROR: Empty conditional argument\n")
						os.Exit(1)
					}
					ch := str[0]
					// uses element as second argument
					orig := str
					if ch == '#' || ch == '%' || ch == '^' {
						// check for pound, percent, or caret character at beginning of element (undocumented)
						str = str[1:]
						if len(str) < 1 {
							fmt.Fprintf(os.Stderr, "\nERROR: Unexpected conditional constraints\n")
							os.Exit(1)
						}
						ch = str[0]
					}
					if (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') {
						prnt, match := SplitInTwoAt(str, "/", RIGHT)
						match, attrib := SplitInTwoAt(match, "@", LEFT)
						wildcard := false
						if strings.HasPrefix(prnt, ":") || strings.HasPrefix(match, ":") || strings.HasPrefix(attrib, ":") {
							wildcard = true
						}
						tsk := &Step{Type: status, Value: orig, Parent: prnt, Match: match, Attrib: attrib, Wild: wildcard}
						op.Stages = append(op.Stages, tsk)
					} else {
						fmt.Fprintf(os.Stderr, "\nERROR: Unexpected conditional constraints\n")
						os.Exit(1)
					}
					op = nil
				}
				status = UNSET
			case GT, GE, LT, LE, EQ, NE:
				if op != nil {
					if len(str) > 1 && str[0] == '\\' {
						// first character may be backslash protecting minus sign (undocumented)
						str = str[1:]
					}
					if len(str) < 1 {
						fmt.Fprintf(os.Stderr, "\nERROR: Empty numeric match constraints\n")
						os.Exit(1)
					}
					ch := str[0]
					if (ch >= '0' && ch <= '9') || ch == '-' || ch == '+' {
						// literal numeric constant
						tsk := &Step{Type: status, Value: str}
						op.Stages = append(op.Stages, tsk)
					} else {
						// numeric test allows element as second argument
						orig := str
						if ch == '#' || ch == '%' || ch == '^' {
							// check for pound, percent, or caret character at beginning of element (undocumented)
							str = str[1:]
							if len(str) < 1 {
								fmt.Fprintf(os.Stderr, "\nERROR: Unexpected numeric match constraints\n")
								os.Exit(1)
							}
							ch = str[0]
						}
						if (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') {
							prnt, match := SplitInTwoAt(str, "/", RIGHT)
							match, attrib := SplitInTwoAt(match, "@", LEFT)
							wildcard := false
							if strings.HasPrefix(prnt, ":") || strings.HasPrefix(match, ":") || strings.HasPrefix(attrib, ":") {
								wildcard = true
							}
							tsk := &Step{Type: status, Value: orig, Parent: prnt, Match: match, Attrib: attrib, Wild: wildcard}
							op.Stages = append(op.Stages, tsk)
						} else {
							fmt.Fprintf(os.Stderr, "\nERROR: Unexpected numeric match constraints\n")
							os.Exit(1)
						}
					}
					op = nil
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unexpected adjacent numeric match constraints\n")
					os.Exit(1)
				}
				status = UNSET
			case UNRECOGNIZED:
				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized argument '%s'\n", str)
				os.Exit(1)
			default:
				fmt.Fprintf(os.Stderr, "\nERROR: Unexpected argument '%s'\n", str)
				os.Exit(1)
			}
		}

		return cond
	}

	parseExtractions := func(cmds *Block, arguments []string) []*Operation {

		max := len(arguments)
		if max < 1 {
			return nil
		}

		// check for missing -element (or -first, etc.) command
		txt := arguments[0]
		if len(txt) < 1 || txt[0] != '-' {
			fmt.Fprintf(os.Stderr, "\nERROR: Missing -element command before '%s'\n", txt)
			os.Exit(1)
		}
		// check for missing argument after last -element (or -first, etc.) command
		txt = arguments[max-1]
		if len(txt) > 0 && txt[0] == '-' {
			if txt == "-rst" {
				fmt.Fprintf(os.Stderr, "\nERROR: Unexpected position for %s command\n", txt)
				os.Exit(1)
			} else if txt == "-clr" {
				// main loop runs out after trailing -clr, add another so this one will be executed
				arguments = append(arguments, "-clr")
				max++
			} else if max < 2 || arguments[max-2] != "-lbl" {
				fmt.Fprintf(os.Stderr, "\nERROR: Item missing after %s command\n", txt)
				os.Exit(1)
			}
		}

		comm := make([]*Operation, 0, max)

		// parse next argument
		nextStatus := func(str string) OpType {

			status := ParseFlag(str)

			switch status {
			case VARIABLE:
				op := &Operation{Type: status, Value: str[1:]}
				comm = append(comm, op)
				status = VALUE
			case CLR, RST:
				op := &Operation{Type: status, Value: ""}
				comm = append(comm, op)
				status = UNSET
			case ELEMENT, FIRST, LAST, ENCODE, DECODE, PLAIN, UPPER, LOWER, CHAIN, TITLE, ORDER, YEAR, TRANSLATE, TERMS, WORDS, PAIRS, REVERSE, LETTERS, CLAUSES, INDICES, MESHCODE, MATRIX, HISTOGRAM, ACCENTED:
			case NUM, LEN, SUM, MIN, MAX, INC, DEC, SUB, AVG, DEV, MED, MUL, DIV, MOD, BIN, BIT, ZEROBASED, ONEBASED, UCSCBASED, REVCOMP, NUCLEIC, FASTA, MOLWT:
			case TAB, RET, PFX, SFX, SEP, LBL, PFC, DEQ, PLG, ELG, WRP, DEF, COLOR:
			case FWD, AWD:
			case UNSET:
				fmt.Fprintf(os.Stderr, "\nERROR: No -element before '%s'\n", str)
				os.Exit(1)
			case UNRECOGNIZED:
				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized argument '%s'\n", str)
				os.Exit(1)
			default:
				fmt.Fprintf(os.Stderr, "\nERROR: Misplaced %s command\n", str)
				os.Exit(1)
			}

			return status
		}

		// parse extraction clause into individual steps
		parseSteps := func(op *Operation, pttrn string) {

			if op == nil {
				return
			}

			stat := op.Type
			str := op.Value

			// element names combined with commas are treated as a prefix-separator-suffix group
			comma := strings.Split(str, ",")

			rnge := ""
			for _, item := range comma {
				status := stat

				// isolate and parse optional [min:max], [&VAR:&VAR], or [after|before] range specification
				item, rnge = SplitInTwoAt(item, "[", LEFT)

				item = strings.TrimSpace(item)
				rnge = strings.TrimSpace(rnge)

				if item == "" && rnge != "" {
					fmt.Fprintf(os.Stderr, "\nERROR: Variable missing in range specification [%s\n", rnge)
					os.Exit(1)
				}

				typL, strL, intL, typR, strR, intR := parseRange(item, rnge)

				// check for special character at beginning of name
				if len(item) > 1 {
					switch item[0] {
					case '&':
						if IsAllCapsOrDigits(item[1:]) {
							status = VARIABLE
							item = item[1:]
						} else {
							fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized variable '%s'\n", item)
							os.Exit(1)
						}
					case '#':
						status = COUNT
						item = item[1:]
					case '%':
						status = LENGTH
						item = item[1:]
					case '^':
						status = DEPTH
						item = item[1:]
					case '*':
						for _, ch := range item {
							if ch != '*' {
								break
							}
						}
						status = STAR
					default:
					}
				} else {
					switch item {
					case "?":
						status = QUESTION
					case "*":
						status = STAR
					case "$":
						status = DOLLAR
					case "@":
						status = ATSIGN
					case "+":
						status = INDEX
					default:
					}
				}

				// parse parent/element@attribute construct
				// colon indicates a namespace prefix in any or all of the components
				prnt, match := SplitInTwoAt(item, "/", RIGHT)
				match, attrib := SplitInTwoAt(match, "@", LEFT)

				// leading colon indicates namespace prefix wildcard
				wildcard := false
				if strings.HasPrefix(prnt, ":") || strings.HasPrefix(match, ":") || strings.HasPrefix(attrib, ":") {
					wildcard = true
				}

				// sequence coordinate adjustments
				switch status {
				case ZEROBASED, ONEBASED, UCSCBASED:
					seq := pttrn + ":"
					if attrib != "" {
						seq += "@"
						seq += attrib
					} else if match != "" {
						seq += match
					}
					// confirm -0-based or -1-based arguments are known sequence position elements or attributes
					slock.RLock()
					seqtype, ok := sequenceTypeIs[seq]
					slock.RUnlock()
					if !ok {
						fmt.Fprintf(os.Stderr, "\nERROR: Element '%s' is not suitable for sequence coordinate conversion\n", item)
						os.Exit(1)
					}
					switch status {
					case ZEROBASED:
						status = ELEMENT
						// if 1-based coordinates, decrement to get 0-based value
						if seqtype.Based == 1 {
							status = DEC
						}
					case ONEBASED:
						status = ELEMENT
						// if 0-based coordinates, increment to get 1-based value
						if seqtype.Based == 0 {
							status = INC
						}
					case UCSCBASED:
						status = ELEMENT
						// half-open intervals, start is 0-based, stop is 1-based
						if seqtype.Based == 0 && seqtype.Which == ISSTOP {
							status = INC
						} else if seqtype.Based == 1 && seqtype.Which == ISSTART {
							status = DEC
						}
					default:
						status = ELEMENT
					}
				default:
				}

				norm := true
				if rnge != "" {
					if typL != NORANGE || typR != NORANGE || strL != "" || strR != "" || intL != 0 || intR != 0 {
						norm = false
					}
				}

				tsk := &Step{Type: status, Value: item, Parent: prnt, Match: match, Attrib: attrib,
					TypL: typL, StrL: strL, IntL: intL, TypR: typR, StrR: strR, IntR: intR,
					Norm: norm, Wild: wildcard}

				op.Stages = append(op.Stages, tsk)
			}
		}

		idx := 0

		status := UNSET

		// parse command strings into operation structure
		for idx < max {
			str := arguments[idx]
			idx++

			if argTypeIs[str] == CONDITIONAL {
				fmt.Fprintf(os.Stderr, "\nERROR: Misplaced %s command\n", str)
				os.Exit(1)
			}

			switch status {
			case UNSET:
				status = nextStatus(str)
			case ELEMENT, FIRST, LAST, ENCODE, DECODE, PLAIN, UPPER, LOWER, CHAIN, TITLE, ORDER, YEAR, TRANSLATE, TERMS, WORDS, PAIRS, REVERSE, LETTERS, CLAUSES, INDICES, MESHCODE, MATRIX, HISTOGRAM, ACCENTED,
				NUM, LEN, SUM, MIN, MAX, INC, DEC, SUB, AVG, DEV, MED, MUL, DIV, MOD, BIN, BIT, ZEROBASED, ONEBASED, UCSCBASED, REVCOMP, NUCLEIC, FASTA, MOLWT:
				for !strings.HasPrefix(str, "-") {
					// create one operation per argument, even if under a single -element statement
					op := &Operation{Type: status, Value: str}
					comm = append(comm, op)
					parseSteps(op, pttrn)
					if idx >= max {
						break
					}
					str = arguments[idx]
					idx++
				}
				status = UNSET
				if idx < max {
					status = nextStatus(str)
				}
			case TAB, RET, PFX, SFX, SEP, LBL, PFC, DEQ, PLG, ELG, WRP, DEF, COLOR:
				op := &Operation{Type: status, Value: ConvertSlash(str)}
				comm = append(comm, op)
				status = UNSET
			case FWD:
				cmds.Foreword = ConvertSlash(str)
				status = UNSET
			case AWD:
				cmds.Afterword = ConvertSlash(str)
				status = UNSET
			case VARIABLE:
				op := &Operation{Type: status, Value: str[1:]}
				comm = append(comm, op)
				status = VALUE
			case VALUE:
				op := &Operation{Type: status, Value: str}
				comm = append(comm, op)
				parseSteps(op, pttrn)
				status = UNSET
			case UNRECOGNIZED:
				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized argument '%s'\n", str)
				os.Exit(1)
			default:
			}
		}

		return comm
	}

	// parseOperations recursive definition
	var parseOperations func(parent *Block)

	// parseOperations converts parsed arguments to operations lists
	parseOperations = func(parent *Block) {

		args := parent.Parsed

		partition := 0
		for cur, str := range args {

			// record junction between conditional and extraction commands
			partition = cur + 1

			// skip if not a command
			if len(str) < 1 || str[0] != '-' {
				continue
			}

			if argTypeIs[str] != CONDITIONAL {
				partition = cur
				break
			}
		}

		// split arguments into conditional tests and extraction or customization commands
		conditionals := args[0:partition]
		args = args[partition:]

		partition = 0
		foundElse := false
		for cur, str := range args {

			// record junction at -else command
			partition = cur + 1

			// skip if not a command
			if len(str) < 1 || str[0] != '-' {
				continue
			}

			if str == "-else" {
				partition = cur
				foundElse = true
				break
			}
		}

		extractions := args[0:partition]
		alternative := args[partition:]

		if len(alternative) > 0 && alternative[0] == "-else" {
			alternative = alternative[1:]
		}

		// validate argument structure and convert to operations lists
		parent.Conditions = parseConditionals(parent, conditionals)
		parent.Commands = parseExtractions(parent, extractions)
		parent.Failure = parseExtractions(parent, alternative)

		// reality checks on placement of -else command
		if foundElse {
			if len(conditionals) < 1 {
				fmt.Fprintf(os.Stderr, "\nERROR: Misplaced -else command\n")
				os.Exit(1)
			}
			if len(alternative) < 1 {
				fmt.Fprintf(os.Stderr, "\nERROR: Misplaced -else command\n")
				os.Exit(1)
			}
			if len(parent.Subtasks) > 0 {
				fmt.Fprintf(os.Stderr, "\nERROR: Misplaced -else command\n")
				os.Exit(1)
			}
		}

		for _, sub := range parent.Subtasks {
			parseOperations(sub)
		}
	}

	// ParseArguments

	head := &Block{}

	for _, txt := range cmdargs {
		head.Working = append(head.Working, txt)
	}

	// initial parsing of exploration command structure
	parseCommands(head, PATTERN)

	if len(head.Subtasks) != 1 {
		return nil
	}

	// skip past empty placeholder
	head = head.Subtasks[0]

	// convert command strings to array of operations for faster processing
	parseOperations(head)

	// check for no -element or multiple -pattern commands
	noElement := true
	numPatterns := 0
	for _, txt := range cmdargs {
		if argTypeIs[txt] == EXTRACTION {
			noElement = false
		}
		if txt == "-pattern" || txt == "-Pattern" {
			numPatterns++
		} else if txt == "-select" {
			noElement = false
			head.Position = "select"
		}
	}

	if numPatterns < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: No -pattern in command-line arguments\n")
		os.Exit(1)
	}

	if numPatterns > 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: Only one -pattern command is permitted\n")
		os.Exit(1)
	}

	if noElement {
		fmt.Fprintf(os.Stderr, "\nERROR: No -element statement in argument list\n")
		os.Exit(1)
	}

	return head
}

// ExploreElements returns matching element values to callback
func ExploreElements(curr *Node, mask, prnt, match, attrib string, wildcard, unescape bool, level int, proc func(string, int)) {

	if curr == nil || proc == nil {
		return
	}

	// **/Object performs deep exploration of recursive data (*/Object also supported)
	deep := false
	if prnt == "**" || prnt == "*" {
		prnt = ""
		deep = true
	}

	var exploreChildren func(curr *Node, acc func(string))

	exploreChildren = func(curr *Node, acc func(string)) {

		if curr.Contents != "" {
			acc(curr.Contents)
		}
		for chld := curr.Children; chld != nil; chld = chld.Next {
			if chld.Name != "" {
				acc("<" + chld.Name + ">")
			}
			exploreChildren(chld, acc)
			if chld.Name != "" {
				acc("</" + chld.Name + ">")
			}
		}
	}

	// exploreElements recursive definition
	var exploreElements func(curr *Node, skip string, lev int)

	exploreElements = func(curr *Node, skip string, lev int) {

		if !deep && curr.Name == skip {
			// do not explore within recursive object
			return
		}

		if curr.Name == match ||
			// parent/* matches any subfield
			(match == "*" && prnt != "") ||
			// wildcard (internal colon) matches any namespace prefix
			(wildcard && strings.HasPrefix(match, ":") && strings.HasSuffix(curr.Name, match)) ||
			(match == "" && attrib != "") {

			if prnt == "" ||
				curr.Parent == prnt ||
				(wildcard && strings.HasPrefix(prnt, ":") && strings.HasSuffix(curr.Parent, prnt)) {

				if attrib != "" {
					if curr.Attributes != "" && curr.Attribs == nil {
						// parse attributes on-the-fly if queried
						curr.Attribs = ParseAttributes(curr.Attributes)
					}
					for i := 0; i < len(curr.Attribs)-1; i += 2 {
						// attributes now parsed into array as [ tag, value, tag, value, tag, value, ... ]
						if curr.Attribs[i] == attrib ||
							(wildcard && strings.HasPrefix(attrib, ":") && strings.HasSuffix(curr.Attribs[i], attrib)) {
							proc(curr.Attribs[i+1], level)
							return
						}
					}

				} else if curr.Contents != "" {

					str := curr.Contents[:]

					if unescape && HasAmpOrNotASCII(str) {
						// processing of <, >, &, ", and ' characters is now delayed until element contents is requested
						str = html.UnescapeString(str)
					}

					proc(str, level)
					return

				} else if curr.Children != nil {

					if DoMixed {
						// match with mixed contents - send all child strings
						var buffer strings.Builder
						exploreChildren(curr, func(str string) {
							if str != "" {
								buffer.WriteString(str)
							}
						})
						str := buffer.String()

						// clean up reconstructed mixed content
						str = DoTrimFlankingHTML(str)
						if HasBadSpace(str) {
							str = CleanupBadSpaces(str)
						}
						if HasAdjacentSpaces(str) {
							str = CompressRunsOfSpaces(str)
						}
						if NeedsTightening(str) {
							str = TightenParentheses(str)
						}
						if unescape && HasAmpOrNotASCII(str) {
							str = html.UnescapeString(str)
						}

						proc(str, level)
						return
					}

					// for XML container object, send empty string to callback to increment count
					proc("", level)
					// and continue exploring

				} else if curr.Attributes != "" {

					// for self-closing object, indicate presence by sending empty string to callback
					proc("", level)
					return
				}
			}
		}

		for chld := curr.Children; chld != nil; chld = chld.Next {
			// inner exploration is subject to recursive object exclusion
			exploreElements(chld, mask, lev+1)
		}
	}

	exploreElements(curr, "", level)
}

// PrintSubtree supports compression styles selected by -element "*" through "****"
func PrintSubtree(node *Node, style IndentType, printAttrs bool, proc func(string)) {

	if node == nil || proc == nil {
		return
	}

	// WRAPPED is SUBTREE plus each attribute on its own line
	wrapped := false
	if style == WRAPPED {
		style = SUBTREE
		wrapped = true
	}

	// INDENT is offset by two spaces to allow for parent tag, SUBTREE is not offset
	initial := 1
	if style == SUBTREE {
		style = INDENT
		initial = 0
	}

	// array to speed up indentation
	indentSpaces := []string{
		"",
		"  ",
		"    ",
		"      ",
		"        ",
		"          ",
		"            ",
		"              ",
		"                ",
		"                  ",
	}

	// indent a specified number of spaces
	doIndent := func(indt int) {
		i := indt
		for i > 9 {
			proc("                    ")
			i -= 10
		}
		if i < 0 {
			return
		}
		proc(indentSpaces[i])
	}

	// doSubtree recursive definition
	var doSubtree func(*Node, int)

	doSubtree = func(curr *Node, depth int) {

		// suppress if it would be an empty self-closing tag
		if !IsNotJustWhitespace(curr.Attributes) && curr.Contents == "" && curr.Children == nil {
			return
		}

		if style == INDENT {
			doIndent(depth)
		}

		if curr.Name != "" {
			proc("<")
			proc(curr.Name)

			if printAttrs {

				attr := strings.TrimSpace(curr.Attributes)
				attr = CompressRunsOfSpaces(attr)

				if attr != "" {

					if wrapped {

						start := 0
						idx := 0

						attlen := len(attr)

						for idx < attlen {
							ch := attr[idx]
							if ch == '=' {
								str := attr[start:idx]
								proc("\n")
								doIndent(depth)
								proc(" ")
								proc(str)
								// skip past equal sign and leading double quote
								idx += 2
								start = idx
							} else if ch == '"' || ch == '\'' {
								str := attr[start:idx]
								proc("=\"")
								proc(str)
								proc("\"")
								// skip past trailing double quote and (possible) space
								idx += 2
								start = idx
							} else {
								idx++
							}
						}

						proc("\n")
						doIndent(depth)

					} else {

						proc(" ")
						proc(attr)
					}
				}
			}

			// see if suitable for for self-closing tag
			if curr.Contents == "" && curr.Children == nil {
				proc("/>")
				if style != COMPACT {
					proc("\n")
				}
				return
			}

			proc(">")
		}

		if curr.Contents != "" {

			proc(curr.Contents[:])

		} else {

			if style != COMPACT {
				proc("\n")
			}

			for chld := curr.Children; chld != nil; chld = chld.Next {
				doSubtree(chld, depth+1)
			}

			if style == INDENT {
				i := depth
				for i > 9 {
					proc("                    ")
					i -= 10
				}
				proc(indentSpaces[i])
			}
		}

		if curr.Name != "" {
			proc("<")
			proc("/")
			proc(curr.Name)
			proc(">")
		}

		if style != COMPACT {
			proc("\n")
		}
	}

	doSubtree(node, initial)
}

// ProcessClause handles comma-separated -element arguments
func ProcessClause(curr *Node, stages []*Step, mask, prev, pfx, sfx, plg, sep, def string, status OpType, index, level int, variables map[string]string, transform map[string]string, histogram map[string]int) (string, bool) {

	if curr == nil || stages == nil {
		return "", false
	}

	// reverseComplement reverse-complements a nucleotide sequence
	reverseComplement := func(str string) string {

		runes := []rune(str)
		// reverse sequence letters - middle base in odd-length sequence is not touched, so cannot also complement here
		for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
			runes[i], runes[j] = runes[j], runes[i]
		}
		found := false
		// now complement every base, also handling uracil, leaving case intact
		for i, ch := range runes {
			runes[i], found = revComp[ch]
			if !found {
				runes[i] = 'X'
			}
		}
		str = string(runes)

		return str
	}

	// proteinWeight adds the molecular weight of each amino acid
	proteinWeight := func(str string) string {

		// Start with water (H2O)
		c := 0
		h := 2
		n := 0
		o := 1
		s := 0
		se := 0

		// remove leading methionine
		str = strings.ToUpper(str)
		str = strings.TrimPrefix(str, "M")

		runes := []rune(str)
		// add number of carbon, hydrogen, nitrogen, oxygen, sulfur, and selenium atoms per amino acid
		for _, ch := range runes {
			c += numC[ch]
			h += numH[ch]
			n += numN[ch]
			o += numO[ch]
			s += numS[ch]
			se += numSe[ch]
		}

		// calculate molecular weight
		wt := 12.01115*float64(c) + 1.0079*float64(h) + 14.0067*float64(n) + 15.9994*float64(o) + 32.064*float64(s) + 78.96*float64(se)

		str = strconv.Itoa(int(wt + 0.5))

		return str
	}

	// processElement handles individual -element constructs
	processElement := func(acc func(string)) {

		if acc == nil {
			return
		}

		// element names combined with commas are treated as a prefix-separator-suffix group
		for _, stage := range stages {

			stat := stage.Type
			item := stage.Value
			prnt := stage.Parent
			match := stage.Match
			attrib := stage.Attrib
			typL := stage.TypL
			strL := stage.StrL
			intL := stage.IntL
			typR := stage.TypR
			strR := stage.StrR
			intR := stage.IntR
			norm := stage.Norm
			wildcard := stage.Wild
			unescape := (stat != INDICES)

			// exploreElements is a wrapper for ExploreElements, obtaining most arguments as closures
			exploreElements := func(proc func(string, int)) {
				ExploreElements(curr, mask, prnt, match, attrib, wildcard, unescape, level, proc)
			}

			// sendSlice applies optional [min:max] range restriction and sends result to accumulator
			sendSlice := func(str string) {

				// handle usual situation with no range first
				if norm {
					acc(str)
					return
				}

				// check for [after|before] variant
				if typL == STRINGRANGE || typR == STRINGRANGE {
					if strL != "" {
						// use case-insensitive test
						strL = strings.ToUpper(strL)
						idx := strings.Index(strings.ToUpper(str), strL)
						if idx < 0 {
							// specified substring must be present in original string
							return
						}
						ln := len(strL)
						// remove leading text
						str = str[idx+ln:]
					}
					if strR != "" {
						strR = strings.ToUpper(strR)
						idx := strings.Index(strings.ToUpper(str), strR)
						if idx < 0 {
							// specified substring must be present in remaining string
							return
						}
						// remove trailing text
						str = str[:idx]
					}
					if str != "" {
						acc(str)
					}
					return
				}

				min := 0
				max := 0

				// slice arguments use variable value +- adjustment or integer constant
				if typL == VARIABLERANGE {
					if strL == "" {
						return
					}
					lft, ok := variables[strL]
					if !ok {
						return
					}
					val, err := strconv.Atoi(lft)
					if err != nil {
						return
					}
					// range argument values are inclusive and 1-based, decrement variable start +- offset to use in slice
					min = val + intL - 1
				} else if typL == INTEGERRANGE {
					// range argument values are inclusive and 1-based, decrement literal start to use in slice
					min = intL - 1
				}
				if typR == VARIABLERANGE {
					if strR == "" {
						return
					}
					rgt, ok := variables[strR]
					if !ok {
						return
					}
					val, err := strconv.Atoi(rgt)
					if err != nil {
						return
					}
					if val+intR < 0 {
						// negative value is 1-based inset from end of string (undocumented)
						max = len(str) + val + intR + 1
					} else {
						max = val + intR
					}
				} else if typR == INTEGERRANGE {
					if intR < 0 {
						// negative max is inset from end of string (undocumented)
						max = len(str) + intR + 1
					} else {
						max = intR
					}
				}

				doRevComp := false
				doUpCase := false
				if status == NUCLEIC {
					// -nucleic uses direction of range to decide between forward strand or reverse complement
					if min+1 > max {
						min, max = max-1, min+1
						doRevComp = true
					}
					doUpCase = true
				}

				// numeric range now calculated, apply slice to string
				if min == 0 && max == 0 {
					if doRevComp {
						str = reverseComplement(str)
					}
					if doUpCase {
						str = strings.ToUpper(str)
					}
					acc(str)
				} else if max == 0 {
					if min > 0 && min < len(str) {
						str = str[min:]
						if str != "" {
							if doRevComp {
								str = reverseComplement(str)
							}
							if doUpCase {
								str = strings.ToUpper(str)
							}
							acc(str)
						}
					}
				} else if min == 0 {
					if max > 0 && max <= len(str) {
						str = str[:max]
						if str != "" {
							if doRevComp {
								str = reverseComplement(str)
							}
							if doUpCase {
								str = strings.ToUpper(str)
							}
							acc(str)
						}
					}
				} else {
					if min < max && min > 0 && max <= len(str) {
						str = str[min:max]
						if str != "" {
							if doRevComp {
								str = reverseComplement(str)
							}
							if doUpCase {
								str = strings.ToUpper(str)
							}
							acc(str)
						}
					}
				}
			}

			switch stat {
			case ELEMENT:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						sendSlice(str)
					}
				})
			case TERMS, WORDS, PAIRS, REVERSE, LETTERS, CLAUSES, INDICES, MESHCODE, MATRIX, HISTOGRAM, ACCENTED,
				VALUE, LEN, SUM, MIN, MAX, SUB, AVG, DEV, MED, MUL, DIV, MOD, BIN, BIT, REVCOMP, NUCLEIC, FASTA, MOLWT:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						sendSlice(str)
					}
				})
			case FIRST:
				single := ""

				exploreElements(func(str string, lvl int) {
					if single == "" {
						single = str
					}
				})

				if single != "" {
					sendSlice(single)
				}
			case LAST:
				single := ""

				exploreElements(func(str string, lvl int) {
					single = str
				})

				if single != "" {
					sendSlice(single)
				}
			case ENCODE:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						str = html.EscapeString(str)
						sendSlice(str)
					}
				})
			case DECODE:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						txt, err := base64.StdEncoding.DecodeString(str)
						if err == nil {
							sendSlice(string(txt))
						}
					}
				})
			case PLAIN:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						if IsNotASCII(str) {
							str = DoAccentTransform(str)
							if HasUnicodeMarkup(str) {
								str = RepairUnicodeMarkup(str, SPACE)
							}
						}
						if HasBadSpace(str) {
							str = CleanupBadSpaces(str)
						}
						if HasAngleBracket(str) {
							str = RepairTableMarkup(str, SPACE)
							str = RemoveEmbeddedMarkup(str)
							str = CompressRunsOfSpaces(str)
						}
						sendSlice(str)
					}
				})
			case UPPER:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						str = strings.ToUpper(str)
						sendSlice(str)
					}
				})
			case LOWER:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						str = strings.ToLower(str)
						sendSlice(str)
					}
				})
			case CHAIN:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						str = strings.Replace(str, " ", "_", -1)
						sendSlice(str)
					}
				})
			case TITLE:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						str = strings.ToLower(str)
						str = strings.Title(str)
						sendSlice(str)
					}
				})
			case ORDER:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						str = SortStringByWords(str)
						sendSlice(str)
					}
				})
			case YEAR:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						words := strings.FieldsFunc(str, func(c rune) bool {
							return !unicode.IsDigit(c)
						})
						for _, item := range words {
							if len(item) == 4 {
								sendSlice(item)
								// only print first year, e.g., PubDate/MedlineDate "2008 Dec-2009 Jan"
								return
							}
						}
					}
				})
			case TRANSLATE:
				exploreElements(func(str string, lvl int) {
					if str != "" {
						txt, found := transform[str]
						if found {
							// require successful mapping
							sendSlice(txt)
						}
					}
				})
			case VARIABLE:
				// use value of stored variable
				val, ok := variables[match]
				if ok {
					sendSlice(val)
				}
			case NUM, COUNT:
				count := 0

				exploreElements(func(str string, lvl int) {
					count++
				})

				// number of element objects
				val := strconv.Itoa(count)
				acc(val)
			case LENGTH:
				length := 0

				exploreElements(func(str string, lvl int) {
					length += len(str)
				})

				// length of element strings
				val := strconv.Itoa(length)
				acc(val)
			case DEPTH:
				exploreElements(func(str string, lvl int) {
					// depth of each element in scope
					val := strconv.Itoa(lvl)
					acc(val)
				})
			case INDEX:
				// -element "+" prints index of current XML object
				val := strconv.Itoa(index)
				acc(val)
			case INC:
				// -inc, or component of -0-based, -1-based, or -ucsc-based
				exploreElements(func(str string, lvl int) {
					if str != "" {
						num, err := strconv.Atoi(str)
						if err == nil {
							// increment value
							num++
							val := strconv.Itoa(num)
							acc(val)
						}
					}
				})
			case DEC:
				// -dec, or component of -0-based, -1-based, or -ucsc-based
				exploreElements(func(str string, lvl int) {
					if str != "" {
						num, err := strconv.Atoi(str)
						if err == nil {
							// decrement value
							num--
							val := strconv.Itoa(num)
							acc(val)
						}
					}
				})
			case QUESTION:
				acc(curr.Name)
			case STAR:
				// -element "*" prints current XML subtree on a single line
				style := SINGULARITY
				printAttrs := true

				for _, ch := range item {
					if ch == '*' {
						style++
					} else if ch == '@' {
						printAttrs = false
					}
				}
				if style > WRAPPED {
					style = WRAPPED
				}
				if style < COMPACT {
					style = COMPACT
				}

				var buffer strings.Builder

				PrintSubtree(curr, style, printAttrs,
					func(str string) {
						if str != "" {
							buffer.WriteString(str)
						}
					})

				txt := buffer.String()
				if txt != "" {
					acc(txt)
				}
			case DOLLAR:
				for chld := curr.Children; chld != nil; chld = chld.Next {
					acc(chld.Name)
				}
			case ATSIGN:
				if curr.Attributes != "" && curr.Attribs == nil {
					curr.Attribs = ParseAttributes(curr.Attributes)
				}
				for i := 0; i < len(curr.Attribs)-1; i += 2 {
					acc(curr.Attribs[i])
				}
			default:
			}
		}
	}

	ok := false

	// format results in buffer
	var buffer strings.Builder

	buffer.WriteString(prev)
	buffer.WriteString(plg)
	buffer.WriteString(pfx)
	between := ""

	switch status {
	case ELEMENT:
		processElement(func(str string) {
			if str != "" {
				ok = true
				buffer.WriteString(between)
				buffer.WriteString(str)
				between = sep
			}
		})
	case FIRST:
		single := ""

		processElement(func(str string) {
			ok = true
			if single == "" {
				single = str
			}
		})

		if single != "" {
			buffer.WriteString(between)
			buffer.WriteString(single)
			between = sep
		}
	case LAST:
		single := ""

		processElement(func(str string) {
			ok = true
			single = str
		})

		if single != "" {
			buffer.WriteString(between)
			buffer.WriteString(single)
			between = sep
		}
	case ENCODE, DECODE, PLAIN, UPPER, LOWER, CHAIN, TITLE, ORDER, YEAR, TRANSLATE, VALUE, NUM, INC, DEC, ZEROBASED, ONEBASED, UCSCBASED, NUCLEIC:
		processElement(func(str string) {
			if str != "" {
				ok = true
				buffer.WriteString(between)
				buffer.WriteString(str)
				between = sep
			}
		})
	case LEN:
		length := 0

		processElement(func(str string) {
			length += len(str)
			ok = true
		})

		if ok {
			// length of element strings
			val := strconv.Itoa(length)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case SUM:
		sum := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				sum += value
				ok = true
			}
		})

		if ok {
			// sum of element values
			val := strconv.Itoa(sum)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case MIN:
		min := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				if !ok || value < min {
					min = value
				}
				ok = true
			}
		})

		if ok {
			// minimum of element values
			val := strconv.Itoa(min)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case MAX:
		max := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				if !ok || value > max {
					max = value
				}
				ok = true
			}
		})

		if ok {
			// maximum of element values
			val := strconv.Itoa(max)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case SUB:
		first := 0
		second := 0
		count := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				count++
				if count == 1 {
					first = value
				} else if count == 2 {
					second = value
				}
			}
		})

		if count == 2 {
			// must have exactly 2 elements
			ok = true
			// difference of element values
			val := strconv.Itoa(first - second)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case AVG:
		sum := 0
		count := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				sum += value
				count++
				ok = true
			}
		})

		if ok {
			// average of element values
			avg := int(float64(sum) / float64(count))
			val := strconv.Itoa(avg)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case DEV:
		count := 0
		mean := 0.0
		m2 := 0.0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				// Welford algorithm for one-pass standard deviation
				count++
				x := float64(value)
				delta := x - mean
				mean += delta / float64(count)
				m2 += delta * (x - mean)
			}
		})

		if count > 1 {
			// must have at least 2 elements
			ok = true
			// standard deviation of element values
			vrc := m2 / float64(count-1)
			dev := int(math.Sqrt(vrc))
			val := strconv.Itoa(dev)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case MED:
		var arry []int
		count := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				arry = append(arry, value)
				count++
				ok = true
			}
		})

		if ok {
			// median of element values
			sort.Slice(arry, func(i, j int) bool { return arry[i] < arry[j] })
			med := arry[count/2]
			val := strconv.Itoa(med)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case MUL:
		first := 0
		second := 0
		count := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				count++
				if count == 1 {
					first = value
				} else if count == 2 {
					second = value
				}
			}
		})

		if count == 2 {
			// must have exactly 2 elements
			ok = true
			// product of element values
			val := strconv.Itoa(first * second)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case DIV:
		first := 0
		second := 0
		count := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				count++
				if count == 1 {
					first = value
				} else if count == 2 {
					second = value
				}
			}
		})

		if count == 2 {
			// must have exactly 2 elements
			ok = true
			// quotient of element values
			val := strconv.Itoa(first / second)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case MOD:
		first := 0
		second := 0
		count := 0

		processElement(func(str string) {
			value, err := strconv.Atoi(str)
			if err == nil {
				count++
				if count == 1 {
					first = value
				} else if count == 2 {
					second = value
				}
			}
		})

		if count == 2 {
			// must have exactly 2 elements
			ok = true
			// modulus of element values
			val := strconv.Itoa(first % second)
			buffer.WriteString(between)
			buffer.WriteString(val)
			between = sep
		}
	case BIN:
		processElement(func(str string) {
			num, err := strconv.Atoi(str)
			if err == nil {
				// convert to binary representation
				val := strconv.FormatInt(int64(num), 2)
				buffer.WriteString(between)
				buffer.WriteString(val)
				between = sep
				ok = true
			}
		})
	case BIT:
		processElement(func(str string) {
			num, err := strconv.Atoi(str)
			if err == nil {
				// Kernighan algorithm for counting set bits
				count := 0
				for num != 0 {
					num &= num - 1
					count++
				}
				val := strconv.Itoa(count)
				buffer.WriteString(between)
				buffer.WriteString(val)
				between = sep
				ok = true
			}
		})
	case REVCOMP:
		processElement(func(str string) {
			if str != "" {
				ok = true
				buffer.WriteString(between)
				str = reverseComplement(str)
				buffer.WriteString(str)
				between = sep
			}
		})
	case FASTA:
		processElement(func(str string) {
			for str != "" {
				mx := len(str)
				if mx > 50 {
					mx = 50
				}
				item := str[:mx]
				str = str[mx:]
				ok = true
				buffer.WriteString(between)
				buffer.WriteString(item)
				between = sep
			}
		})
	case MOLWT:
		processElement(func(str string) {
			if str != "" {
				ok = true
				buffer.WriteString(between)
				str = proteinWeight(str)
				buffer.WriteString(str)
				between = sep
			}
		})
	case INDICES:
		norm := make(map[string][]string)
		stem := make(map[string][]string)

		cumulative := 0

		// mutex for inverted index
		var ilock sync.Mutex

		addItem := func(field map[string][]string, term string, position int) {

			// protect with mutex
			ilock.Lock()

			arry, found := field[term]
			if !found {
				arry = make([]string, 0, 1)
			}
			arry = append(arry, strconv.Itoa(position))
			field[term] = arry

			ilock.Unlock()
		}

		processElement(func(str string) {

			if str == "" {
				return
			}

			if str == "[Not Available]." {
				return
			}

			if IsNotASCII(str) {
				str = DoAccentTransform(str)
				if HasUnicodeMarkup(str) {
					str = RepairUnicodeMarkup(str, SPACE)
				}
			}

			str = strings.ToLower(str)

			if HasBadSpace(str) {
				str = CleanupBadSpaces(str)
			}
			if HasAngleBracket(str) {
				str = RepairEncodedMarkup(str)
				str = RepairTableMarkup(str, SPACE)
				str = RepairScriptMarkup(str, SPACE)
				str = RepairMathMLMarkup(str, SPACE)
				// RemoveEmbeddedMarkup must be called before UnescapeString, which was suppressed in ExploreElements
				str = RemoveEmbeddedMarkup(str)
			}

			if HasAmpOrNotASCII(str) {
				str = html.UnescapeString(str)
				str = strings.ToLower(str)
			}

			if IsNotASCII(str) {
				if HasGreek(str) {
					str = SpellGreek(str)
					str = CompressRunsOfSpaces(str)
				}
			}

			str = strings.Replace(str, "(", " ", -1)
			str = strings.Replace(str, ")", " ", -1)

			str = strings.Replace(str, "_", " ", -1)

			if HasHyphenOrApostrophe(str) {
				str = FixSpecialCases(str)
			}

			str = strings.Replace(str, "-", " ", -1)

			// remove trailing punctuation from each word
			var arry []string

			terms := strings.Fields(str)
			for _, item := range terms {
				max := len(item)
				for max > 1 {
					ch := item[max-1]
					if ch != '.' && ch != ',' && ch != ':' && ch != ';' {
						break
					}
					// trim trailing period, comma, colon, and semicolon
					item = item[:max-1]
					// continue checking for runs of punctuation at end
					max--
				}
				if item == "" {
					continue
				}
				arry = append(arry, item)
			}

			// rejoin into string
			cleaned := strings.Join(arry, " ")

			// break clauses at punctuation other than space or underscore, and at non-ASCII characters
			clauses := strings.FieldsFunc(cleaned, func(c rune) bool {
				return (!unicode.IsLetter(c) && !unicode.IsDigit(c)) && c != ' ' && c != '_' || c > 127
			})

			// space replaces plus sign to separate runs of unpunctuated words
			phrases := strings.Join(clauses, " ")

			// break phrases into individual words
			words := strings.Fields(phrases)

			for _, item := range words {

				cumulative++

				// skip at site of punctuation break
				if item == "+" {
					continue
				}

				// skip terms that are all digits
				if IsAllDigitsOrPeriod(item) {
					continue
				}

				// optional stop word removal
				if DeStop && IsStopWord(item) {
					continue
				}

				// index single normalized term
				addItem(norm, item, cumulative)
				ok = true

				// apply stemming algorithm
				item = porter2.Stem(item)
				item = strings.TrimSpace(item)
				addItem(stem, item, cumulative)
			}

			// pad to avoid false positive proximity match of words in adjacent paragraphs
			rounded := ((cumulative + 99) / 100) * 100
			if rounded-cumulative < 20 {
				rounded += 100
			}
			cumulative = rounded
		})

		prepareIndices := func(field map[string][]string, label string) {

			if len(field) < 1 {
				return
			}

			var arry []string

			for item := range field {
				arry = append(arry, item)
			}

			sort.Slice(arry, func(i, j int) bool { return arry[i] < arry[j] })

			last := ""
			for _, item := range arry {
				item = strings.TrimSpace(item)
				if item == "" {
					continue
				}
				if item == last {
					// skip duplicate entry
					continue
				}
				buffer.WriteString("      <")
				buffer.WriteString(label)
				if len(field[item]) > 0 {
					buffer.WriteString(" pos=\"")
					attr := strings.Join(field[item], ",")
					buffer.WriteString(attr)
					buffer.WriteString("\"")
				}
				buffer.WriteString(">")
				buffer.WriteString(item)
				buffer.WriteString("</")
				buffer.WriteString(label)
				buffer.WriteString(">\n")
				last = item
			}
		}

		if ok {
			prepareIndices(norm, "NORM")
			prepareIndices(stem, "STEM")
		}
	case TERMS:
		processElement(func(str string) {
			if str != "" {

				terms := strings.Fields(str)
				for _, item := range terms {
					max := len(item)
					for max > 1 {
						ch := item[max-1]
						if ch != '.' && ch != ',' && ch != ':' && ch != ';' {
							break
						}
						// trim trailing period, comma, colon, and semicolon
						item = item[:max-1]
						// continue checking for runs of punctuation at end
						max--
					}
					if item == "" {
						continue
					}
					ok = true
					buffer.WriteString(between)
					buffer.WriteString(item)
					between = sep
				}
			}
		})
	case WORDS:
		processElement(func(str string) {
			if str != "" {

				words := strings.FieldsFunc(str, func(c rune) bool {
					return !unicode.IsLetter(c) && !unicode.IsDigit(c)
				})
				for _, item := range words {
					item = strings.ToLower(item)
					if DeStop {
						if IsStopWord(item) {
							continue
						}
					}
					if DoStem {
						item = porter2.Stem(item)
						item = strings.TrimSpace(item)
					}
					if item == "" {
						continue
					}
					ok = true
					buffer.WriteString(between)
					buffer.WriteString(item)
					between = sep
				}
			}
		})
	case PAIRS:
		processElement(func(str string) {
			if str != "" {

				// break clauses at punctuation other than space or underscore, and at non-ASCII characters
				clauses := strings.FieldsFunc(str, func(c rune) bool {
					return (!unicode.IsLetter(c) && !unicode.IsDigit(c)) && c != ' ' || c > 127
				})

				// plus sign separates runs of unpunctuated words
				phrases := strings.Join(clauses, " + ")

				// break phrases into individual words
				words := strings.FieldsFunc(phrases, func(c rune) bool {
					return !unicode.IsLetter(c) && !unicode.IsDigit(c)
				})

				if len(words) > 1 {
					past := ""
					for _, item := range words {
						if item == "+" {
							past = ""
							continue
						}
						item = strings.ToLower(item)
						if DeStop {
							if IsStopWord(item) {
								past = ""
								continue
							}
						}
						if DoStem {
							item = porter2.Stem(item)
							item = strings.TrimSpace(item)
						}
						if item == "" {
							past = ""
							continue
						}
						if past != "" {
							ok = true
							buffer.WriteString(between)
							buffer.WriteString(past + " " + item)
							between = sep
						}
						past = item
					}
				}
			}
		})
	case REVERSE:
		processElement(func(str string) {
			if str != "" {

				words := strings.FieldsFunc(str, func(c rune) bool {
					return !unicode.IsLetter(c) && !unicode.IsDigit(c)
				})
				for lf, rt := 0, len(words)-1; lf < rt; lf, rt = lf+1, rt-1 {
					words[lf], words[rt] = words[rt], words[lf]
				}
				for _, item := range words {
					item = strings.ToLower(item)
					if DeStop {
						if IsStopWord(item) {
							continue
						}
					}
					if DoStem {
						item = porter2.Stem(item)
						item = strings.TrimSpace(item)
					}
					if item == "" {
						continue
					}
					ok = true
					buffer.WriteString(between)
					buffer.WriteString(item)
					between = sep
				}
			}
		})
	case LETTERS:
		processElement(func(str string) {
			if str != "" {
				for _, ch := range str {
					ok = true
					buffer.WriteString(between)
					buffer.WriteRune(ch)
					between = sep
				}
			}
		})
	case CLAUSES:
		processElement(func(str string) {
			if str != "" {

				clauses := strings.FieldsFunc(str, func(c rune) bool {
					return c == '.' || c == ',' || c == ';' || c == ':'
				})
				for _, item := range clauses {
					item = strings.ToLower(item)
					item = strings.TrimSpace(item)
					if item == "" {
						continue
					}
					ok = true
					buffer.WriteString(between)
					buffer.WriteString(item)
					between = sep
				}
			}
		})
	case MESHCODE:
		var code []string
		var tree []string

		processElement(func(str string) {
			if str != "" {
				txt, found := transform[str]
				str = strings.ToLower(str)
				code = append(code, str)
				ok = true

				if !found {
					return
				}
				txt = strings.ToLower(txt)
				txt = strings.Replace(txt, ".", "_", -1)
				codes := strings.FieldsFunc(txt, func(c rune) bool {
					return c == ','
				})
				for _, item := range codes {
					ch := item[0]
					if item == "" {
						continue
					}
					switch ch {
					case 'a', 'c', 'd', 'e', 'f', 'g', 'z':
						tree = append(tree, item)
					default:
					}
				}
			}
		})

		if len(code) > 1 {
			sort.Slice(code, func(i, j int) bool { return code[i] < code[j] })
		}
		if len(tree) > 1 {
			sort.Slice(tree, func(i, j int) bool { return tree[i] < tree[j] })
		}

		last := ""
		for _, item := range code {
			if item == last {
				// skip duplicate entry
				continue
			}
			buffer.WriteString("      <CODE>")
			buffer.WriteString(item)
			buffer.WriteString("</CODE>\n")
			last = item
		}

		last = ""
		for _, item := range tree {
			if item == last {
				// skip duplicate entry
				continue
			}
			buffer.WriteString("      <TREE>")
			buffer.WriteString(item)
			buffer.WriteString("</TREE>\n")
			last = item
		}
	case MATRIX:
		var arry []string

		processElement(func(str string) {
			if str != "" {
				txt, found := transform[str]
				if found {
					str = txt
				}
				arry = append(arry, str)
				ok = true
			}
		})

		if len(arry) > 1 {
			sort.Slice(arry, func(i, j int) bool { return arry[i] < arry[j] })

			for i, frst := range arry {
				for j, scnd := range arry {
					if i == j {
						continue
					}
					buffer.WriteString(between)
					buffer.WriteString(frst)
					buffer.WriteString("\t")
					buffer.WriteString(scnd)
					between = "\n"
				}
			}
		}
	case HISTOGRAM:
		processElement(func(str string) {
			if str != "" {
				ok = true

				hlock.Lock()

				val := histogram[str]
				val++
				histogram[str] = val

				hlock.Unlock()
			}
		})
	case ACCENTED:
		processElement(func(str string) {
			if str != "" {
				found := false
				for _, ch := range str {
					if ch > 127 {
						found = true
						break
					}
				}
				if found {
					ok = true
					buffer.WriteString(between)
					buffer.WriteString(str)
					between = sep
				}
			}
		})
	default:
	}

	// use default value if nothing written
	if !ok && def != "" {
		ok = true
		buffer.WriteString(def)
	}

	buffer.WriteString(sfx)

	if !ok {
		return "", false
	}

	txt := buffer.String()

	return txt, true
}

// ProcessInstructions performs extraction commands on a subset of XML
func ProcessInstructions(commands []*Operation, curr *Node, mask, tab, ret string, index, level int, variables map[string]string, transform map[string]string, histogram map[string]int, accum func(string)) (string, string) {

	if accum == nil {
		return tab, ret
	}

	sep := "\t"
	pfx := ""
	sfx := ""
	plg := ""
	elg := ""
	lst := ""

	def := ""

	col := "\t"
	lin := "\n"

	varname := ""

	plain := true
	var currColor *color.Color

	// handles color, e.g., -color "red,bold", reset to plain by -color "-" (undocumented)
	printInColor := func(str string) {
		if plain || currColor == nil {
			accum(str)
		} else {
			tx := currColor.SprintFunc()
			tmp := fmt.Sprintf("%s", tx(str))
			accum(tmp)
		}
	}

	// process commands
	for _, op := range commands {

		str := op.Value

		switch op.Type {
		case ELEMENT, FIRST, LAST, ENCODE, DECODE, PLAIN, UPPER, LOWER, CHAIN, TITLE, ORDER, YEAR, TRANSLATE, TERMS, WORDS, PAIRS, REVERSE, LETTERS, CLAUSES, INDICES, MESHCODE, MATRIX, ACCENTED,
			NUM, LEN, SUM, MIN, MAX, INC, DEC, SUB, AVG, DEV, MED, MUL, DIV, MOD, BIN, BIT, ZEROBASED, ONEBASED, UCSCBASED, REVCOMP, NUCLEIC, FASTA, MOLWT:
			txt, ok := ProcessClause(curr, op.Stages, mask, tab, pfx, sfx, plg, sep, def, op.Type, index, level, variables, transform, histogram)
			if ok {
				plg = ""
				lst = elg
				tab = col
				ret = lin
				if plain {
					accum(txt)
				} else {
					printInColor(txt)
				}
			}
		case HISTOGRAM:
			txt, ok := ProcessClause(curr, op.Stages, mask, "", "", "", "", "", "", op.Type, index, level, variables, transform, histogram)
			if ok {
				accum(txt)
			}
		case TAB:
			col = str
		case RET:
			lin = str
		case PFX:
			pfx = str
		case SFX:
			sfx = str
		case SEP:
			sep = str
		case LBL:
			lbl := str
			accum(tab)
			accum(plg)
			accum(pfx)
			if plain {
				accum(lbl)
			} else {
				printInColor(lbl)
			}
			accum(sfx)
			plg = ""
			lst = elg
			tab = col
			ret = lin
		case PFC:
			// preface clears previous tab and sets prefix in one command
			pfx = str
			fallthrough
		case CLR:
			// clear previous tab after the fact
			tab = ""
		case DEQ:
			// set queued tab after the fact
			tab = str
		case PLG:
			plg = str
		case ELG:
			elg = str
		case WRP:
			// shortcut to wrap elements in XML tags
			if str == "" || str == "-" {
				sep = "\t"
				pfx = ""
				sfx = ""
				plg = ""
				elg = ""
				break
			}
			lft, rgt := SplitInTwoAt(str, ",", RIGHT)
			if lft != "" {
				plg = "<" + lft + ">"
				elg = "</" + lft + ">"
			}
			if rgt != "" && rgt != "-" {
				pfx = "<" + rgt + ">"
				sfx = "</" + rgt + ">"
				sep = "</" + rgt + "><" + rgt + ">"
			}
		case RST:
			pfx = ""
			sfx = ""
			plg = ""
			elg = ""
			sep = "\t"
			def = ""
		case DEF:
			def = str
		case COLOR:
			currColor = color.New()
			if str == "-" || str == "reset" || str == "clear" {
				plain = true
				break
			}
			plain = false
			items := strings.Split(str, ",")
			for _, itm := range items {
				switch itm {
				case "red":
					currColor.Add(color.FgRed)
				case "grn", "green":
					currColor.Add(color.FgGreen)
				case "blu", "blue":
					currColor.Add(color.FgBlue)
				case "blk", "black":
					currColor.Add(color.FgBlack)
				case "bld", "bold":
					currColor.Add(color.Bold)
				case "ital", "italic", "italics":
					currColor.Add(color.Italic)
				case "blink", "flash":
					currColor.Add(color.BlinkSlow)
				default:
					fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized color argument '%s'\n", itm)
					os.Exit(1)
				}
			}
		case VARIABLE:
			varname = str
		case VALUE:
			length := len(str)
			if length > 1 && str[0] == '(' && str[length-1] == ')' {
				// set variable from literal text inside parentheses, e.g., -COM "(, )"
				variables[varname] = str[1 : length-1]
				// -if "&VARIABLE" will succeed if set to blank with empty parentheses "()"
			} else if str == "" {
				// -if "&VARIABLE" will fail if initialized with empty string ""
				delete(variables, varname)
			} else {
				txt, ok := ProcessClause(curr, op.Stages, mask, "", pfx, sfx, plg, sep, def, op.Type, index, level, variables, transform, histogram)
				if ok {
					plg = ""
					lst = elg
					variables[varname] = txt
				}
			}
			varname = ""
		default:
		}
	}

	if plain {
		accum(lst)
	} else {
		printInColor(lst)
	}

	return tab, ret
}

// CONDITIONAL EXECUTION USES -if AND -unless STATEMENT, WITH SUPPORT FOR DEPRECATED -match AND -avoid STATEMENTS

// ConditionsAreSatisfied tests a set of conditions to determine if extraction should proceed
func ConditionsAreSatisfied(conditions []*Operation, curr *Node, mask string, index, level int, variables map[string]string) bool {

	if curr == nil {
		return false
	}

	required := 0
	observed := 0
	forbidden := 0
	isMatch := false
	isAvoid := false

	// matchFound tests individual conditions
	matchFound := func(stages []*Step) bool {

		if stages == nil || len(stages) < 1 {
			return false
		}

		stage := stages[0]

		var constraint *Step

		if len(stages) > 1 {
			constraint = stages[1]
		}

		status := stage.Type
		prnt := stage.Parent
		match := stage.Match
		attrib := stage.Attrib
		typL := stage.TypL
		strL := stage.StrL
		intL := stage.IntL
		typR := stage.TypR
		strR := stage.StrR
		intR := stage.IntR
		norm := stage.Norm
		wildcard := stage.Wild
		unescape := true

		found := false
		number := ""

		// exploreElements is a wrapper for ExploreElements, obtaining most arguments as closures
		exploreElements := func(proc func(string, int)) {
			ExploreElements(curr, mask, prnt, match, attrib, wildcard, unescape, level, proc)
		}

		// test string or numeric constraints
		testConstraint := func(str string) bool {

			if str == "" || constraint == nil {
				return false
			}

			val := constraint.Value
			stat := constraint.Type

			switch stat {
			case EQUALS, CONTAINS, ISWITHIN, STARTSWITH, ENDSWITH, ISNOT, ISBEFORE, ISAFTER, MATCHES, RESEMBLES:
				// substring test on element values
				str = strings.ToUpper(str)
				val = strings.ToUpper(val)

				switch stat {
				case EQUALS:
					if str == val {
						return true
					}
				case CONTAINS:
					if strings.Contains(str, val) {
						return true
					}
				case ISWITHIN:
					if strings.Contains(val, str) {
						return true
					}
				case STARTSWITH:
					if strings.HasPrefix(str, val) {
						return true
					}
				case ENDSWITH:
					if strings.HasSuffix(str, val) {
						return true
					}
				case ISNOT:
					if str != val {
						return true
					}
				case ISBEFORE:
					if str < val {
						return true
					}
				case ISAFTER:
					if str > val {
						return true
					}
				case MATCHES:
					if RemoveCommaOrSemicolon(str) == strings.ToLower(val) {
						return true
					}
				case RESEMBLES:
					if SortStringByWords(str) == strings.ToLower(val) {
						return true
					}
				default:
				}
			case ISEQUALTO, DIFFERSFROM:
				// conditional argument is element specifier
				if constraint.Parent != "" || constraint.Match != "" || constraint.Attrib != "" {
					ch := val[0]
					// pound, percent, and caret prefixes supported (undocumented)
					switch ch {
					case '#':
						count := 0
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							count++
						})
						val = strconv.Itoa(count)
					case '%':
						length := 0
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							if stn != "" {
								length += len(stn)
							}
						})
						val = strconv.Itoa(length)
					case '^':
						depth := 0
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							depth = lvl
						})
						val = strconv.Itoa(depth)
					default:
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							if stn != "" {
								val = stn
							}
						})
					}
				}
				str = strings.ToUpper(str)
				val = strings.ToUpper(val)

				switch stat {
				case ISEQUALTO:
					if str == val {
						return true
					}
				case DIFFERSFROM:
					if str != val {
						return true
					}
				default:
				}
			case GT, GE, LT, LE, EQ, NE:
				// second argument of numeric test can be element specifier
				if constraint.Parent != "" || constraint.Match != "" || constraint.Attrib != "" {
					ch := val[0]
					// pound, percent, and caret prefixes supported as potentially useful for data QA (undocumented)
					switch ch {
					case '#':
						count := 0
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							count++
						})
						val = strconv.Itoa(count)
					case '%':
						length := 0
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							if stn != "" {
								length += len(stn)
							}
						})
						val = strconv.Itoa(length)
					case '^':
						depth := 0
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							depth = lvl
						})
						val = strconv.Itoa(depth)
					default:
						ExploreElements(curr, mask, constraint.Parent, constraint.Match, constraint.Attrib, constraint.Wild, true, level, func(stn string, lvl int) {
							if stn != "" {
								_, errz := strconv.Atoi(stn)
								if errz == nil {
									val = stn
								}
							}
						})
					}
				}

				// numeric tests on element values
				x, errx := strconv.Atoi(str)
				y, erry := strconv.Atoi(val)

				// both arguments must resolve to integers
				if errx != nil || erry != nil {
					return false
				}

				switch stat {
				case GT:
					if x > y {
						return true
					}
				case GE:
					if x >= y {
						return true
					}
				case LT:
					if x < y {
						return true
					}
				case LE:
					if x <= y {
						return true
					}
				case EQ:
					if x == y {
						return true
					}
				case NE:
					if x != y {
						return true
					}
				default:
				}
			default:
			}

			return false
		}

		// checkConstraint applies optional [min:max] range restriction and sends result to testConstraint
		checkConstraint := func(str string) bool {

			// handle usual situation with no range first
			if norm {
				return testConstraint(str)
			}

			// check for [after|before] variant
			if typL == STRINGRANGE || typR == STRINGRANGE {
				if strL != "" {
					// use case-insensitive test
					strL = strings.ToUpper(strL)
					idx := strings.Index(strings.ToUpper(str), strL)
					if idx < 0 {
						// specified substring must be present in original string
						return false
					}
					ln := len(strL)
					// remove leading text
					str = str[idx+ln:]
				}
				if strR != "" {
					strR = strings.ToUpper(strR)
					idx := strings.Index(strings.ToUpper(str), strR)
					if idx < 0 {
						// specified substring must be present in remaining string
						return false
					}
					// remove trailing text
					str = str[:idx]
				}
				if str != "" {
					return testConstraint(str)
				}
				return false
			}

			min := 0
			max := 0

			// slice arguments use variable value +- adjustment or integer constant
			if typL == VARIABLERANGE {
				if strL == "" {
					return false
				}
				lft, ok := variables[strL]
				if !ok {
					return false
				}
				val, err := strconv.Atoi(lft)
				if err != nil {
					return false
				}
				// range argument values are inclusive and 1-based, decrement variable start +- offset to use in slice
				min = val + intL - 1
			} else if typL == INTEGERRANGE {
				// range argument values are inclusive and 1-based, decrement literal start to use in slice
				min = intL - 1
			}
			if typR == VARIABLERANGE {
				if strR == "" {
					return false
				}
				rgt, ok := variables[strR]
				if !ok {
					return false
				}
				val, err := strconv.Atoi(rgt)
				if err != nil {
					return false
				}
				if val+intR < 0 {
					// negative value is 1-based inset from end of string (undocumented)
					max = len(str) + val + intR + 1
				} else {
					max = val + intR
				}
			} else if typR == INTEGERRANGE {
				if intR < 0 {
					// negative max is inset from end of string (undocumented)
					max = len(str) + intR + 1
				} else {
					max = intR
				}
			}

			// numeric range now calculated, apply slice to string
			if min == 0 && max == 0 {
				return testConstraint(str)
			} else if max == 0 {
				if min > 0 && min < len(str) {
					str = str[min:]
					if str != "" {
						return testConstraint(str)
					}
				}
			} else if min == 0 {
				if max > 0 && max <= len(str) {
					str = str[:max]
					if str != "" {
						return testConstraint(str)
					}
				}
			} else {
				if min < max && min > 0 && max <= len(str) {
					str = str[min:max]
					if str != "" {
						return testConstraint(str)
					}
				}
			}

			return false
		}

		switch status {
		case ELEMENT:
			exploreElements(func(str string, lvl int) {
				// match to XML container object sends empty string, so do not check for str != "" here
				// test every selected element individually if value is specified
				if constraint == nil || checkConstraint(str) {
					found = true
				}
			})
		case VARIABLE:
			// use value of stored variable
			str, ok := variables[match]
			if ok {
				//  -if &VARIABLE -equals VALUE is the supported construct
				if constraint == nil || checkConstraint(str) {
					found = true
				}
			}
		case COUNT:
			count := 0

			exploreElements(func(str string, lvl int) {
				count++
				found = true
			})

			// number of element objects
			number = strconv.Itoa(count)
		case LENGTH:
			length := 0

			exploreElements(func(str string, lvl int) {
				length += len(str)
				found = true
			})

			// length of element strings
			number = strconv.Itoa(length)
		case DEPTH:
			depth := 0

			exploreElements(func(str string, lvl int) {
				depth = lvl
				found = true
			})

			// depth of last element in scope
			number = strconv.Itoa(depth)
		case INDEX:
			// index of explored parent object
			number = strconv.Itoa(index)
			found = true
		default:
		}

		if number == "" {
			return found
		}

		if constraint == nil || checkConstraint(number) {
			return true
		}

		return false
	}

	// test conditional arguments
	for _, op := range conditions {

		switch op.Type {
		// -if tests for presence of element (deprecated -match can test element:value)
		case SELECT, IF, MATCH:
			// checking for failure here allows for multiple -if [ -and / -or ] clauses
			if isMatch && observed < required {
				return false
			}
			if isAvoid && forbidden > 0 {
				return false
			}
			required = 0
			observed = 0
			forbidden = 0
			isMatch = true
			isAvoid = false
			// continue on to next two cases
			fallthrough
		case AND:
			required++
			// continue on to next case
			fallthrough
		case OR:
			if matchFound(op.Stages) {
				observed++
				// record presence of forbidden element if in -unless clause
				forbidden++
			}
		// -unless tests for absence of element, or presence but with failure of subsequent value test (deprecated -avoid can test element:value)
		case UNLESS, AVOID:
			if isMatch && observed < required {
				return false
			}
			if isAvoid && forbidden > 0 {
				return false
			}
			required = 0
			observed = 0
			forbidden = 0
			isMatch = false
			isAvoid = true
			if matchFound(op.Stages) {
				forbidden++
			}
		default:
		}
	}

	if isMatch && observed < required {
		return false
	}
	if isAvoid && forbidden > 0 {
		return false
	}

	return true
}

// RECURSIVELY PROCESS EXPLORATION COMMANDS AND XML DATA STRUCTURE

// ProcessCommands visits XML nodes, performs conditional tests, and executes data extraction instructions
func ProcessCommands(cmds *Block, curr *Node, tab, ret string, index, level int, variables map[string]string, transform map[string]string, histogram map[string]int, accum func(string)) (string, string) {

	if accum == nil {
		return tab, ret
	}

	prnt := cmds.Parent
	match := cmds.Match

	// leading colon indicates namespace prefix wildcard
	wildcard := false
	if strings.HasPrefix(prnt, ":") || strings.HasPrefix(match, ":") {
		wildcard = true
	}

	// **/Object performs deep exploration of recursive data
	deep := false
	if prnt == "**" {
		prnt = "*"
		deep = true
	}
	// Object/** performs exhaustive exploration of nodes
	tall := false
	if match == "**" {
		match = "*"
		tall = true
	}

	// closure passes local variables to callback, which can modify caller tab and ret values
	processNode := func(node *Node, idx, lvl int) {

		// apply -if or -unless tests
		if ConditionsAreSatisfied(cmds.Conditions, node, match, idx, lvl, variables) {

			// execute data extraction commands
			if len(cmds.Commands) > 0 {
				tab, ret = ProcessInstructions(cmds.Commands, node, match, tab, ret, idx, lvl, variables, transform, histogram, accum)
			}

			// process sub commands on child node
			for _, sub := range cmds.Subtasks {
				tab, ret = ProcessCommands(sub, node, tab, ret, 1, lvl, variables, transform, histogram, accum)
			}

		} else {

			// execute commands after -else statement
			if len(cmds.Failure) > 0 {
				tab, ret = ProcessInstructions(cmds.Failure, node, match, tab, ret, idx, lvl, variables, transform, histogram, accum)
			}
		}
	}

	// exploreNodes recursive definition
	var exploreNodes func(*Node, int, int, bool, func(*Node, int, int)) int

	// exploreNodes visits all nodes that match the selection criteria
	exploreNodes = func(curr *Node, indx, levl int, force bool, proc func(*Node, int, int)) int {

		if curr == nil || proc == nil {
			return indx
		}

		// match is "*" for heterogeneous data constructs, e.g., -group PubmedArticleSet/*
		// wildcard matches any namespace prefix
		if curr.Name == match ||
			match == "*" ||
			(wildcard && strings.HasPrefix(match, ":") && strings.HasSuffix(curr.Name, match)) {

			if prnt == "" ||
				curr.Parent == prnt ||
				force ||
				(wildcard && strings.HasPrefix(prnt, ":") && strings.HasSuffix(curr.Parent, prnt)) {

				proc(curr, indx, levl)
				indx++

				if tall && prnt != "" {
					// exhaustive exploration of child nodes within region of parent match
					for chld := curr.Children; chld != nil; chld = chld.Next {
						indx = exploreNodes(chld, indx, levl+1, true, proc)
					}
				}

				if !deep {
					// do not explore within recursive object
					return indx
				}
			}
		}

		// clearing prnt "*" now allows nested exploration within recursive data, e.g., -pattern Taxon -block */Taxon
		if prnt == "*" {
			prnt = ""
		}

		// explore child nodes
		for chld := curr.Children; chld != nil; chld = chld.Next {
			indx = exploreNodes(chld, indx, levl+1, false, proc)
		}

		return indx
	}

	// explorePath recursive definition
	var explorePath func(*Node, []string, int, int, func(*Node, int, int)) int

	// explorePath visits child nodes and matches against next entry in path
	explorePath = func(curr *Node, path []string, indx, levl int, proc func(*Node, int, int)) int {

		if curr == nil || proc == nil {
			return indx
		}

		if len(path) < 1 {
			proc(curr, indx, levl)
			indx++
			return indx
		}

		name := path[0]
		rest := path[1:]

		// explore next level of child nodes
		for chld := curr.Children; chld != nil; chld = chld.Next {
			if chld.Name == name {
				// recurse only if child matches next component in path
				indx = explorePath(chld, rest, indx, levl+1, proc)
			}
		}

		return indx
	}

	if cmds.Foreword != "" {
		accum(cmds.Foreword)
	}

	// apply -position test

	if cmds.Position == "" || cmds.Position == "all" {

		exploreNodes(curr, index, level, false, processNode)

	} else if cmds.Position == "path" {

		exploreNodes(curr, index, level, false,
			func(node *Node, idx, lvl int) {
				// exploreNodes callback has matched first path component, now explore remainder one level and component at a time
				explorePath(node, cmds.Path, idx, lvl, processNode)
			})

	} else {

		var single *Node
		lev := 0
		ind := 0

		if cmds.Position == "first" {

			exploreNodes(curr, index, level, false,
				func(node *Node, idx, lvl int) {
					if single == nil {
						single = node
						ind = idx
						lev = lvl
					}
				})

		} else if cmds.Position == "last" {

			exploreNodes(curr, index, level, false,
				func(node *Node, idx, lvl int) {
					single = node
					ind = idx
					lev = lvl
				})

		} else if cmds.Position == "outer" {

			// print only first and last nodes
			var beg *Limiter
			var end *Limiter

			exploreNodes(curr, index, level, false,
				func(node *Node, idx, lvl int) {
					if beg == nil {
						beg = &Limiter{node, idx, lvl}
					} else {
						end = &Limiter{node, idx, lvl}
					}
				})

			if beg != nil {
				processNode(beg.Obj, beg.Idx, beg.Lvl)
			}
			if end != nil {
				processNode(end.Obj, end.Idx, end.Lvl)
			}

		} else if cmds.Position == "inner" {

			// print all but first and last nodes
			var prev *Limiter
			var next *Limiter
			first := true

			exploreNodes(curr, index, level, false,
				func(node *Node, idx, lvl int) {
					if first {
						first = false
						return
					}

					prev = next
					next = &Limiter{node, idx, lvl}

					if prev != nil {
						processNode(prev.Obj, prev.Idx, prev.Lvl)
					}
				})

		} else if cmds.Position == "even" {

			okay := false

			exploreNodes(curr, index, level, false,
				func(node *Node, idx, lvl int) {
					if okay {
						processNode(node, idx, lvl)
					}
					okay = !okay
				})

		} else if cmds.Position == "odd" {

			okay := true

			exploreNodes(curr, index, level, false,
				func(node *Node, idx, lvl int) {
					if okay {
						processNode(node, idx, lvl)
					}
					okay = !okay
				})

		} else {

			// use numeric position
			number, err := strconv.Atoi(cmds.Position)
			if err == nil {

				pos := 0

				exploreNodes(curr, index, level, false,
					func(node *Node, idx, lvl int) {
						pos++
						if pos == number {
							single = node
							ind = idx
							lev = lvl
						}
					})

			} else {

				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized position '%s'\n", cmds.Position)
				os.Exit(1)
			}
		}

		if single != nil {
			processNode(single, ind, lev)
		}
	}

	if cmds.Afterword != "" {
		accum(cmds.Afterword)
	}

	return tab, ret
}

// PROCESS ONE XML COMPONENT RECORD

// ProcessQuery perform data extraction driven by command-line arguments
func ProcessQuery(Text, parent string, index int, hd, tl string, transform map[string]string, histogram map[string]int, cmds *Block) string {

	if Text == "" || cmds == nil {
		return ""
	}

	// exit from function will collect garbage of node structure for current XML object
	pat := ParseRecord(Text, parent)

	if pat == nil {
		return ""
	}

	// exit from function will also free map of recorded variables for current -pattern
	variables := make(map[string]string)

	var buffer strings.Builder

	ok := false

	if hd != "" {
		buffer.WriteString(hd)
	}

	ret := ""

	if cmds.Position == "select" {

		if ConditionsAreSatisfied(cmds.Conditions, pat, cmds.Match, index, 1, variables) {
			ok = true
			buffer.WriteString(Text)
			ret = "\n"
		}

	} else {

		// start processing at top of command tree and top of XML subregion selected by -pattern
		_, ret = ProcessCommands(cmds, pat, "", "", index, 1, variables, transform, histogram,
			func(str string) {
				if str != "" {
					ok = true
					buffer.WriteString(str)
				}
			})
	}

	if tl != "" {
		buffer.WriteString(tl)
	}

	if ret != "" {
		ok = true
		buffer.WriteString(ret)
	}

	txt := buffer.String()

	// remove leading newline (-insd -pfx artifact)
	if txt != "" && txt[0] == '\n' {
		txt = txt[1:]
	}

	if !ok {
		return ""
	}

	// return consolidated result string
	return txt
}

// INSDSEQ EXTRACTION COMMAND GENERATOR

// e.g., xtract -insd complete mat_peptide "%peptide" product peptide

// ProcessINSD generates extraction commands for GenBank/RefSeq records in INSDSet format
func ProcessINSD(args []string, isPipe, addDash, doIndex bool) []string {

	// legal GenBank / GenPept / RefSeq features

	features := []string{
		"-10_signal",
		"-35_signal",
		"3'clip",
		"3'UTR",
		"5'clip",
		"5'UTR",
		"allele",
		"assembly_gap",
		"attenuator",
		"Bond",
		"C_region",
		"CAAT_signal",
		"CDS",
		"centromere",
		"conflict",
		"D_segment",
		"D-loop",
		"enhancer",
		"exon",
		"gap",
		"GC_signal",
		"gene",
		"iDNA",
		"intron",
		"J_segment",
		"LTR",
		"mat_peptide",
		"misc_binding",
		"misc_difference",
		"misc_feature",
		"misc_recomb",
		"misc_RNA",
		"misc_signal",
		"misc_structure",
		"mobile_element",
		"modified_base",
		"mRNA",
		"mutation",
		"N_region",
		"ncRNA",
		"old_sequence",
		"operon",
		"oriT",
		"polyA_signal",
		"polyA_site",
		"precursor_RNA",
		"prim_transcript",
		"primer_bind",
		"promoter",
		"propeptide",
		"protein_bind",
		"Protein",
		"RBS",
		"Region",
		"regulatory",
		"rep_origin",
		"repeat_region",
		"repeat_unit",
		"rRNA",
		"S_region",
		"satellite",
		"scRNA",
		"sig_peptide",
		"Site",
		"snoRNA",
		"snRNA",
		"source",
		"stem_loop",
		"STS",
		"TATA_signal",
		"telomere",
		"terminator",
		"tmRNA",
		"transit_peptide",
		"tRNA",
		"unsure",
		"V_region",
		"V_segment",
		"variation",
	}

	// legal GenBank / GenPept / RefSeq qualifiers

	qualifiers := []string{
		"allele",
		"altitude",
		"anticodon",
		"artificial_location",
		"bio_material",
		"bond_type",
		"bound_moiety",
		"breed",
		"calculated_mol_wt",
		"cell_line",
		"cell_type",
		"chloroplast",
		"chromoplast",
		"chromosome",
		"citation",
		"clone_lib",
		"clone",
		"coded_by",
		"codon_start",
		"codon",
		"collected_by",
		"collection_date",
		"compare",
		"cons_splice",
		"country",
		"cultivar",
		"culture_collection",
		"cyanelle",
		"db_xref",
		"derived_from",
		"dev_stage",
		"direction",
		"EC_number",
		"ecotype",
		"encodes",
		"endogenous_virus",
		"environmental_sample",
		"estimated_length",
		"evidence",
		"exception",
		"experiment",
		"focus",
		"frequency",
		"function",
		"gap_type",
		"gdb_xref",
		"gene_synonym",
		"gene",
		"germline",
		"haplogroup",
		"haplotype",
		"host",
		"identified_by",
		"inference",
		"insertion_seq",
		"isolate",
		"isolation_source",
		"kinetoplast",
		"lab_host",
		"label",
		"lat_lon",
		"linkage_evidence",
		"locus_tag",
		"macronuclear",
		"map",
		"mating_type",
		"metagenome_source",
		"metagenomic",
		"mitochondrion",
		"mobile_element_type",
		"mobile_element",
		"mod_base",
		"mol_type",
		"name",
		"nat_host",
		"ncRNA_class",
		"non_functional",
		"note",
		"number",
		"old_locus_tag",
		"operon",
		"organelle",
		"organism",
		"partial",
		"PCR_conditions",
		"PCR_primers",
		"peptide",
		"phenotype",
		"plasmid",
		"pop_variant",
		"product",
		"protein_id",
		"proviral",
		"pseudo",
		"pseudogene",
		"rearranged",
		"recombination_class",
		"region_name",
		"regulatory_class",
		"replace",
		"ribosomal_slippage",
		"rpt_family",
		"rpt_type",
		"rpt_unit_range",
		"rpt_unit_seq",
		"rpt_unit",
		"satellite",
		"segment",
		"sequenced_mol",
		"serotype",
		"serovar",
		"sex",
		"site_type",
		"specific_host",
		"specimen_voucher",
		"standard_name",
		"strain",
		"structural_class",
		"sub_clone",
		"sub_species",
		"sub_strain",
		"submitter_seqid",
		"tag_peptide",
		"tissue_lib",
		"tissue_type",
		"trans_splicing",
		"transcript_id",
		"transcription",
		"transgenic",
		"transl_except",
		"transl_table",
		"translation",
		"transposon",
		"type_material",
		"UniProtKB_evidence",
		"usedin",
		"variety",
		"virion",
	}

	// legal INSDSeq XML fields

	insdtags := []string{
		"INSDAltSeqData_items",
		"INSDAltSeqData",
		"INSDAltSeqItem_first-accn",
		"INSDAltSeqItem_gap-comment",
		"INSDAltSeqItem_gap-length",
		"INSDAltSeqItem_gap-linkage",
		"INSDAltSeqItem_gap-type",
		"INSDAltSeqItem_interval",
		"INSDAltSeqItem_isgap",
		"INSDAltSeqItem_isgap@value",
		"INSDAltSeqItem_last-accn",
		"INSDAltSeqItem_value",
		"INSDAltSeqItem",
		"INSDAuthor",
		"INSDComment_paragraphs",
		"INSDComment_type",
		"INSDComment",
		"INSDCommentParagraph",
		"INSDFeature_intervals",
		"INSDFeature_key",
		"INSDFeature_location",
		"INSDFeature_operator",
		"INSDFeature_partial3",
		"INSDFeature_partial3@value",
		"INSDFeature_partial5",
		"INSDFeature_partial5@value",
		"INSDFeature_quals",
		"INSDFeature_xrefs",
		"INSDFeature",
		"INSDFeatureSet_annot-source",
		"INSDFeatureSet_features",
		"INSDFeatureSet",
		"INSDInterval_accession",
		"INSDInterval_from",
		"INSDInterval_interbp",
		"INSDInterval_interbp@value",
		"INSDInterval_iscomp",
		"INSDInterval_iscomp@value",
		"INSDInterval_point",
		"INSDInterval_to",
		"INSDInterval",
		"INSDKeyword",
		"INSDQualifier_name",
		"INSDQualifier_value",
		"INSDQualifier",
		"INSDReference_authors",
		"INSDReference_consortium",
		"INSDReference_journal",
		"INSDReference_position",
		"INSDReference_pubmed",
		"INSDReference_reference",
		"INSDReference_remark",
		"INSDReference_title",
		"INSDReference_xref",
		"INSDReference",
		"INSDSecondary-accn",
		"INSDSeq_accession-version",
		"INSDSeq_alt-seq",
		"INSDSeq_comment-set",
		"INSDSeq_comment",
		"INSDSeq_contig",
		"INSDSeq_create-date",
		"INSDSeq_create-release",
		"INSDSeq_database-reference",
		"INSDSeq_definition",
		"INSDSeq_division",
		"INSDSeq_entry-version",
		"INSDSeq_feature-set",
		"INSDSeq_feature-table",
		"INSDSeq_keywords",
		"INSDSeq_length",
		"INSDSeq_locus",
		"INSDSeq_moltype",
		"INSDSeq_organism",
		"INSDSeq_other-seqids",
		"INSDSeq_primary-accession",
		"INSDSeq_primary",
		"INSDSeq_project",
		"INSDSeq_references",
		"INSDSeq_secondary-accessions",
		"INSDSeq_segment",
		"INSDSeq_sequence",
		"INSDSeq_source-db",
		"INSDSeq_source",
		"INSDSeq_strandedness",
		"INSDSeq_struc-comments",
		"INSDSeq_taxonomy",
		"INSDSeq_topology",
		"INSDSeq_update-date",
		"INSDSeq_update-release",
		"INSDSeq_xrefs",
		"INSDSeq",
		"INSDSeqid",
		"INSDSet",
		"INSDStrucComment_items",
		"INSDStrucComment_name",
		"INSDStrucComment",
		"INSDStrucCommentItem_tag",
		"INSDStrucCommentItem_url",
		"INSDStrucCommentItem_value",
		"INSDStrucCommentItem",
		"INSDXref_dbname",
		"INSDXref_id",
		"INSDXref",
	}

	checkAgainstVocabulary := func(str, objtype string, arry []string) {

		if str == "" || arry == nil {
			return
		}

		// skip past pound, percent, or caret character at beginning of string
		if len(str) > 1 {
			switch str[0] {
			case '#', '%', '^':
				str = str[1:]
			default:
			}
		}

		for _, txt := range arry {
			if str == txt {
				return
			}
			if strings.ToUpper(str) == strings.ToUpper(txt) {
				fmt.Fprintf(os.Stderr, "\nERROR: Incorrect capitalization of '%s' %s, change to '%s'\n", str, objtype, txt)
				os.Exit(1)
			}
		}

		fmt.Fprintf(os.Stderr, "\nERROR: Item '%s' is not a legal -insd %s\n", str, objtype)
		os.Exit(1)
	}

	var acc []string

	max := len(args)
	if max < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to xtract -insd\n")
		os.Exit(1)
	}

	if doIndex {
		if isPipe {
			acc = append(acc, "-head", "<IdxDocumentSet>", "-tail", "</IdxDocumentSet>")
			acc = append(acc, "-hd", "  <IdxDocument>\n", "-tl", "  </IdxDocument>")
			acc = append(acc, "-pattern", "INSDSeq", "-pfx", "    <IdxUid>", "-sfx", "</IdxUid>\n")
			acc = append(acc, "-element", "INSDSeq_accession-version", "-clr", "-rst", "-tab", "\n")
		} else {
			acc = append(acc, "-head", "\"<IdxDocumentSet>\"", "-tail", "\"</IdxDocumentSet>\"")
			acc = append(acc, "-hd", "\"  <IdxDocument>\\n\"", "-tl", "\"  </IdxDocument>\"")
			acc = append(acc, "-pattern", "INSDSeq", "-pfx", "\"    <IdxUid>\"", "-sfx", "\"</IdxUid>\\n\"")
			acc = append(acc, "-element", "INSDSeq_accession-version", "-clr", "-rst", "-tab", "\\n")
		}
	} else {
		acc = append(acc, "-pattern", "INSDSeq", "-ACCN", "INSDSeq_accession-version", "-SEQ", "INSDSeq_sequence")
	}

	if doIndex {
		if isPipe {
			acc = append(acc, "-group", "INSDSeq", "-lbl", "    <IdxSearchFields>\n")
		} else {
			acc = append(acc, "-group", "INSDSeq", "-lbl", "\"    <IdxSearchFields>\\n\"")
		}
	}

	printAccn := true

	// collect descriptors

	if strings.HasPrefix(args[0], "INSD") {

		if doIndex {
			acc = append(acc, "-clr", "-indices")
		} else {
			if isPipe {
				acc = append(acc, "-clr", "-pfx", "\\n", "-element", "&ACCN")
				acc = append(acc, "-group", "INSDSeq", "-sep", "|", "-element")
			} else {
				acc = append(acc, "-clr", "-pfx", "\"\\n\"", "-element", "\"&ACCN\"")
				acc = append(acc, "-group", "INSDSeq", "-sep", "\"|\"", "-element")
			}
			printAccn = false
		}

		for {
			if len(args) < 1 {
				return acc
			}
			str := args[0]
			if !strings.HasPrefix(args[0], "INSD") {
				break
			}
			checkAgainstVocabulary(str, "element", insdtags)
			acc = append(acc, str)
			args = args[1:]
		}

	} else if strings.HasPrefix(strings.ToUpper(args[0]), "INSD") {

		// report capitalization or vocabulary failure
		checkAgainstVocabulary(args[0], "element", insdtags)

		// program should not get to this point, but warn and exit anyway
		fmt.Fprintf(os.Stderr, "\nERROR: Item '%s' is not a legal -insd %s\n", args[0], "element")
		os.Exit(1)
	}

	// collect qualifiers

	partial := false
	complete := false

	if args[0] == "+" || args[0] == "complete" {
		complete = true
		args = args[1:]
		max--
	} else if args[0] == "-" || args[0] == "partial" {
		partial = true
		args = args[1:]
		max--
	}

	if max < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: No feature key supplied to xtract -insd\n")
		os.Exit(1)
	}

	acc = append(acc, "-group", "INSDFeature")

	// limit to designated features

	feature := args[0]

	fcmd := "-if"

	// can specify multiple features separated by plus sign (e.g., CDS+mRNA) or comma (e.g., CDS,mRNA)
	plus := strings.Split(feature, "+")
	for _, pls := range plus {
		comma := strings.Split(pls, ",")
		for _, cma := range comma {

			checkAgainstVocabulary(cma, "feature", features)
			acc = append(acc, fcmd, "INSDFeature_key", "-equals", cma)

			fcmd = "-or"
		}
	}

	if max < 2 {
		// still need at least one qualifier even on legal feature
		fmt.Fprintf(os.Stderr, "\nERROR: Feature '%s' must be followed by at least one qualifier\n", feature)
		os.Exit(1)
	}

	args = args[1:]

	if complete {
		acc = append(acc, "-unless", "INSDFeature_partial5", "-or", "INSDFeature_partial3")
	} else if partial {
		acc = append(acc, "-if", "INSDFeature_partial5", "-or", "INSDFeature_partial3")
	}

	if printAccn {
		if doIndex {
		} else {
			if isPipe {
				acc = append(acc, "-clr", "-pfx", "\\n", "-element", "&ACCN")
			} else {
				acc = append(acc, "-clr", "-pfx", "\"\\n\"", "-element", "\"&ACCN\"")
			}
		}
	}

	for _, str := range args {

		if str == "mol_wt" {
			str = "calculated_mol_wt"
		}

		if strings.HasPrefix(str, "INSD") {

			checkAgainstVocabulary(str, "element", insdtags)
			if doIndex {
				acc = append(acc, "-block", "INSDFeature", "-clr", "-indices")
			} else {
				if isPipe {
					acc = append(acc, "-block", "INSDFeature", "-sep", "|", "-element")
				} else {
					acc = append(acc, "-block", "INSDFeature", "-sep", "\"|\"", "-element")
				}
			}
			acc = append(acc, str)
			if addDash {
				acc = append(acc, "-block", "INSDFeature", "-unless", str)
				if strings.HasSuffix(str, "@value") {
					if isPipe {
						acc = append(acc, "-lbl", "false")
					} else {
						acc = append(acc, "-lbl", "\"false\"")
					}
				} else {
					if isPipe {
						acc = append(acc, "-lbl", "\\-")
					} else {
						acc = append(acc, "-lbl", "\"\\-\"")
					}
				}
			}

		} else if strings.HasPrefix(str, "#INSD") {

			checkAgainstVocabulary(str, "element", insdtags)
			if doIndex {
				acc = append(acc, "-block", "INSDFeature", "-clr", "-indices")
			} else {
				if isPipe {
					acc = append(acc, "-block", "INSDFeature", "-sep", "|", "-element")
					acc = append(acc, str)
				} else {
					acc = append(acc, "-block", "INSDFeature", "-sep", "\"|\"", "-element")
					ql := fmt.Sprintf("\"%s\"", str)
					acc = append(acc, ql)
				}
			}

		} else if strings.HasPrefix(strings.ToUpper(str), "#INSD") {

			// report capitalization or vocabulary failure
			checkAgainstVocabulary(str, "element", insdtags)

		} else if str == "sub_sequence" {

			// special sub_sequence qualifier shows sequence under feature intervals
			acc = append(acc, "-block", "INSDFeature_intervals")
			if isPipe {
				acc = append(acc, "-clr", "-lbl", "")
			} else {
				acc = append(acc, "-clr", "-lbl", "\"\"")
			}

			acc = append(acc, "-subset", "INSDInterval", "-FR", "INSDInterval_from", "-TO", "INSDInterval_to")
			if isPipe {
				acc = append(acc, "-pfx", "", "-tab", "", "-nucleic", "&SEQ[&FR:&TO]")
			} else {
				acc = append(acc, "-pfx", "\"\"", "-tab", "\"\"", "-nucleic", "\"&SEQ[&FR:&TO]\"")
			}

			acc = append(acc, "-subset", "INSDFeature_intervals")
			if isPipe {
				acc = append(acc, "-deq", "\\t")
			} else {
				acc = append(acc, "-deq", "\"\\t\"")
			}

		} else {

			acc = append(acc, "-block", "INSDQualifier")

			checkAgainstVocabulary(str, "qualifier", qualifiers)
			if len(str) > 2 && str[0] == '%' {
				acc = append(acc, "-if", "INSDQualifier_name", "-equals", str[1:])
				if doIndex {
					if isPipe {
						acc = append(acc, "-clr", "-indices", "%INSDQualifier_value")
					} else {
						acc = append(acc, "-clr", "-indices", "\"%INSDQualifier_value\"")
					}
				} else {
					if isPipe {
						acc = append(acc, "-element", "%INSDQualifier_value")
					} else {
						acc = append(acc, "-element", "\"%INSDQualifier_value\"")
					}
				}
				if addDash {
					acc = append(acc, "-block", "INSDFeature", "-unless", "INSDQualifier_name", "-equals", str[1:])
					if isPipe {
						acc = append(acc, "-lbl", "\\-")
					} else {
						acc = append(acc, "-lbl", "\"\\-\"")
					}
				}
			} else {
				if doIndex {
					acc = append(acc, "-if", "INSDQualifier_name", "-equals", str)
					acc = append(acc, "-clr", "-indices", "INSDQualifier_value")
				} else {
					acc = append(acc, "-if", "INSDQualifier_name", "-equals", str)
					acc = append(acc, "-element", "INSDQualifier_value")
				}
				if addDash {
					acc = append(acc, "-block", "INSDFeature", "-unless", "INSDQualifier_name", "-equals", str)
					if isPipe {
						acc = append(acc, "-lbl", "\\-")
					} else {
						acc = append(acc, "-lbl", "\"\\-\"")
					}
				}
			}
		}
	}

	if doIndex {
		if isPipe {
			acc = append(acc, "-group", "INSDSeq", "-clr", "-lbl", "    </IdxSearchFields>\n")
		} else {
			acc = append(acc, "-group", "INSDSeq", "-clr", "-lbl", "\"    </IdxSearchFields>\\n\"")
		}
	}

	return acc
}

// BIOTHINGS EXTRACTION COMMAND GENERATOR

// ProcessBiopath generates extraction commands for BioThings resources (undocumented)
func ProcessBiopath(args []string, isPipe bool) []string {

	// nquire -get "http://myvariant.info/v1/variant/chr6:g.26093141G>A" \
	//   -fields clinvar.rcv.conditions.identifiers \
	//   -always_list clinvar.rcv.conditions.identifiers |
	// xtract -j2x |
	// xtract -biopath opt clinvar.rcv.conditions.identifiers.omim

	var acc []string

	max := len(args)
	if max < 2 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to xtract -biopath\n")
		os.Exit(1)
	}

	obj := args[0]
	args = args[1:]

	acc = append(acc, "-pattern", obj)

	paths := args[0]

	items := strings.Split(paths, ",")

	for _, path := range items {

		dirs := strings.Split(path, ".")
		max = len(dirs)
		if max < 1 {
			fmt.Fprintf(os.Stderr, "\nERROR: Insufficient path arguments supplied to xtract -biopath\n")
			os.Exit(1)
		}
		if max > 7 {
			fmt.Fprintf(os.Stderr, "\nERROR: Too many nodes in argument supplied to xtract -biopath\n")
			os.Exit(1)
		}

		str := dirs[max-1]

		acc = append(acc, "-path")
		if isPipe {
			acc = append(acc, path)
			acc = append(acc, "-tab", "\\n")
			acc = append(acc, "-element", str)
		} else {
			acc = append(acc, "\""+path+"\"")
			acc = append(acc, "-tab", "\"\\n\"")
			acc = append(acc, "-element", "\""+str+"\"")
		}
	}

	return acc
}

// HYDRA CITATION MATCHER COMMAND GENERATOR

// ProcessHydra generates extraction commands for NCBI's in-house citation matcher (undocumented)
func ProcessHydra(isPipe bool) []string {

	var acc []string

	// acceptable scores are 0.8 or higher, exact match on "1" rejects low value in scientific notation with minus sign present

	acc = append(acc, "-pattern", "Id")
	acc = append(acc, "-if", "@score", "-equals", "1")
	acc = append(acc, "-or", "@score", "-starts-with", "0.9")
	acc = append(acc, "-or", "@score", "-starts-with", "0.8")
	acc = append(acc, "-element", "Id")

	return acc
}

// ENTREZ2INDEX COMMAND GENERATOR

// ProcessE2Index generates extraction commands to create input for Entrez2Index
func ProcessE2Index(args []string, tform string, isPipe bool) []string {

	var acc []string

	max := len(args)
	if max < 3 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to -e2index\n")
		os.Exit(1)
	}

	year := ""
	patrn := args[0]
	args = args[1:]

	if IsAllNumeric(patrn) {
		year = patrn
		patrn = args[0]
		args = args[1:]
	}

	ident := args[0]
	args = args[1:]

	if !isPipe {
		if !DeStop {
			acc = append(acc, "-stops")
		}
		if DoStem {
			acc = append(acc, "-stems")
		}
	}

	if isPipe {
		acc = append(acc, "-head", "<IdxDocumentSet>", "-tail", "</IdxDocumentSet>")
		acc = append(acc, "-hd", "  <IdxDocument>\\n", "-tl", "  </IdxDocument>")
		acc = append(acc, "-pattern")
		acc = append(acc, patrn)
		if year != "" {
			acc = append(acc, "-if", "PubDate/Year", "-ge", year)
			acc = append(acc, "-or", "PubDate/MedlineDate[1:4]", "-ge", year)
		}
		acc = append(acc, "-pfx", "    <IdxUid>", "-sfx", "</IdxUid>\\n")
		acc = append(acc, "-element")
		acc = append(acc, ident)
		acc = append(acc, "-clr", "-rst", "-tab", "")
		acc = append(acc, "-lbl", "    <IdxSearchFields>\\n")
		acc = append(acc, "-pfx", "      <YEAR>", "-sfx", "</YEAR>\\n")
		acc = append(acc, "-year", "PubDate/*")
		acc = append(acc, "-clr", "-rst", "-tab", "")
		acc = append(acc, "-indices")
		for _, str := range args {
			acc = append(acc, str)
		}
		if tform != "" {
			acc = append(acc, "-clr", "-rst", "-tab", "\"\"")
			acc = append(acc, "-sep", ",", "-meshcode")
			acc = append(acc, "MeshHeading/DescriptorName@UI,Chemical/NameOfSubstance@UI,SupplMeshName@UI")
		}
		acc = append(acc, "-clr", "-lbl", "    </IdxSearchFields>\\n")
	} else {
		acc = append(acc, "-head", "\"<IdxDocumentSet>\"", "-tail", "\"</IdxDocumentSet>\"")
		acc = append(acc, "-hd", "\"  <IdxDocument>\\n\"", "-tl", "\"  </IdxDocument>\"")
		acc = append(acc, "-pattern")
		ql := fmt.Sprintf("\"%s\"", patrn)
		acc = append(acc, ql)
		if year != "" {
			acc = append(acc, "-if", "PubDate/Year", "-ge", year)
			acc = append(acc, "-or", "PubDate/MedlineDate[1:4]", "-ge", year)
		}
		acc = append(acc, "-pfx", "\"    <IdxUid>\"", "-sfx", "\"</IdxUid>\\n\"")
		acc = append(acc, "-element")
		ql = fmt.Sprintf("\"%s\"", ident)
		acc = append(acc, ql)
		acc = append(acc, "-clr", "-rst", "-tab", "\"\"")
		acc = append(acc, "-lbl", "\"    <IdxSearchFields>\\n\"")
		acc = append(acc, "-pfx", "\"      <YEAR>\"", "-sfx", "\"</YEAR>\\n\"")
		acc = append(acc, "-year", "\"PubDate/*\"")
		acc = append(acc, "-clr", "-rst", "-tab", "\"\"")
		acc = append(acc, "-indices")
		for _, str := range args {
			ql = fmt.Sprintf("\"%s\"", str)
			acc = append(acc, ql)
		}
		if tform != "" {
			acc = append(acc, "-clr", "-rst", "-tab", "\"\"")
			acc = append(acc, "-sep", "\",\"", "-meshcode")
			acc = append(acc, "\"MeshHeading/DescriptorName@UI,Chemical/NameOfSubstance@UI,SupplMeshName@UI\"")
		}
		acc = append(acc, "-clr", "-lbl", "\"    </IdxSearchFields>\\n\"")
	}

	return acc
}

// CONCURRENT CONSUMER GOROUTINES PARSE AND PROCESS PARTITIONED XML OBJECTS

// StreamBlocks -> SplitPattern => StreamTokens => ParseXML => ProcessQuery -> MergeResults

// processes with single goroutine call defer close(out) so consumer(s) can range over channel
// processes with multiple instances call defer wg.Done(), separate goroutine uses wg.Wait() to delay close(out)

func CreateConsumers(cmds *Block, parent, hd, tl string, transform map[string]string, histogram map[string]int, inp <-chan Extract) <-chan Extract {

	if inp == nil {
		return nil
	}

	out := make(chan Extract, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create consumer channel\n")
		os.Exit(1)
	}

	// xmlConsumer reads partitioned XML from channel and calls parser for processing
	xmlConsumer := func(cmds *Block, parent string, wg *sync.WaitGroup, inp <-chan Extract, out chan<- Extract) {

		// report when this consumer has no more records to process
		defer wg.Done()

		// read partitioned XML from producer channel
		for ext := range inp {

			idx := ext.Index
			text := ext.Text

			if text == "" {
				// should never see empty input data
				out <- Extract{idx, "", text, nil}
				continue
			}

			str := ProcessQuery(text[:], parent, idx, hd, tl, transform, histogram, cmds)

			// send even if empty to get all record counts for reordering
			out <- Extract{idx, "", str, nil}
		}
	}

	var wg sync.WaitGroup

	// launch multiple consumer goroutines
	for i := 0; i < NumServe; i++ {
		wg.Add(1)
		go xmlConsumer(cmds, parent, &wg, inp, out)
	}

	// launch separate anonymous goroutine to wait until all consumers are done
	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

func CreateFormatters(parent string, inp <-chan Extract) <-chan Extract {

	if inp == nil {
		return nil
	}

	out := make(chan Extract, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create formatter channel\n")
		os.Exit(1)
	}

	// xmlFormatter reads partitioned XML from channel and formats on a per-record basis
	xmlFormatter := func(wg *sync.WaitGroup, inp <-chan Extract, out chan<- Extract) {

		// report when this formatter has no more records to process
		defer wg.Done()

		// clean and reformat one record, flush left
		doFormat := func(text string) string {

			var buffer strings.Builder

			// print attributes
			printAttributes := func(attr string) {

				if attr == "" {
					return
				}
				attr = strings.TrimSpace(attr)
				attr = CompressRunsOfSpaces(attr)

				if DeAccent {
					if IsNotASCII(attr) {
						attr = DoAccentTransform(attr)
					}
				}
				if DoASCII {
					if IsNotASCII(attr) {
						attr = UnicodeToASCII(attr)
					}
				}

				buffer.WriteString(" ")
				buffer.WriteString(attr)
			}

			ret := "\n"
			pfx := ""
			skip := 0

			doCleanup := func(tkn Token, nxtTag TagType, nxtName string) {

				if skip > 0 {
					skip--
					return
				}

				name := tkn.Name

				switch tkn.Tag {
				case STARTTAG:
					// convert start-stop to self-closing tag if attributes are present, otherwise skip
					if nxtTag == STOPTAG && nxtName == name {
						if tkn.Attr != "" {
							buffer.WriteString(pfx)
							buffer.WriteString("<")
							buffer.WriteString(name)
							printAttributes(tkn.Attr)
							buffer.WriteString("/>")
							pfx = ret
						}
						skip++
						return
					}
					buffer.WriteString(pfx)
					buffer.WriteString("<")
					buffer.WriteString(name)
					printAttributes(tkn.Attr)
					buffer.WriteString(">")
					pfx = ret
				case SELFTAG:
					if tkn.Attr != "" {
						buffer.WriteString(pfx)
						buffer.WriteString("<")
						buffer.WriteString(name)
						printAttributes(tkn.Attr)
						buffer.WriteString("/>")
						pfx = ret
					}
				case STOPTAG:
					buffer.WriteString(pfx)
					buffer.WriteString("</")
					buffer.WriteString(name)
					buffer.WriteString(">")
					if DoMixed && nxtTag == CONTENTTAG {
						buffer.WriteString(" ")
					}
					pfx = ret
				case CONTENTTAG:
					if nxtTag == STARTTAG || nxtTag == SELFTAG {
						if DoStrict {
							fmt.Fprintf(os.Stderr, "ERROR: UNRECOGNIZED MIXED CONTENT <%s> in <%s>\n", nxtName, name)
						} else if !DoMixed {
							fmt.Fprintf(os.Stderr, "ERROR: UNEXPECTED MIXED CONTENT <%s> in <%s>\n", nxtName, name)
						}
					}
					if len(name) > 0 && IsNotJustWhitespace(name) {
						// support for all content processing flags
						if DoStrict || DoMixed || DoCompress {
							ctype := tkn.Cont
							name = CleanupContents(name, (ctype&ASCII) != 0, (ctype&AMPER) != 0, (ctype&MIXED) != 0)
						}
						buffer.WriteString(name)
					}
					if DoMixed && nxtTag == STARTTAG {
						buffer.WriteString(" ")
					}
					pfx = ""
				case CDATATAG, COMMENTTAG:
					// ignore
				case DOCTYPETAG:
				case NOTAG:
				case ISCLOSED:
					// now handled at end of calling function
				default:
					buffer.WriteString(pfx)
					pfx = ""
				}
			}

			var prev Token
			primed := false

			// track adjacent pairs to give look-ahead at next token
			doPair := func(tkn Token) {

				if primed {
					doCleanup(prev, tkn.Tag, tkn.Name)
				}

				prev = Token{tkn.Tag, tkn.Cont, tkn.Name, tkn.Attr, tkn.Index, tkn.Line}
				primed = true
			}

			ParseXML(text, parent, nil, doPair, nil, nil)

			// isclosed tag
			if primed {
				buffer.WriteString(pfx)
			}

			txt := buffer.String()

			if DoMixed {
				// clean up reconstructed mixed content
				txt = DoTrimFlankingHTML(txt)
				if HasBadSpace(txt) {
					txt = CleanupBadSpaces(txt)
				}
				if HasAdjacentSpaces(txt) {
					txt = CompressRunsOfSpaces(txt)
				}
				if NeedsTightening(txt) {
					txt = TightenParentheses(txt)
				}
			}

			return txt
		}

		// read partitioned XML from producer channel
		for ext := range inp {

			idx := ext.Index
			text := ext.Text

			if text == "" {
				// should never see empty input data
				out <- Extract{idx, "", text, nil}
				continue
			}

			str := doFormat(text[:])

			// send even if empty to get all record counts for reordering
			out <- Extract{idx, "", str, nil}
		}
	}

	var wg sync.WaitGroup

	// launch multiple formatter goroutines
	for i := 0; i < NumServe; i++ {
		wg.Add(1)
		go xmlFormatter(&wg, inp, out)
	}

	// launch separate anonymous goroutine to wait until all formatters are done
	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

func CreateSelectors(parent, indx string, order map[string]bool, inp <-chan Extract) <-chan Extract {

	if parent == "" || indx == "" || order == nil || inp == nil {
		return nil
	}

	find := ParseIndex(indx)

	out := make(chan Extract, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create selector channel\n")
		os.Exit(1)
	}

	// xmlSelector reads partitioned XML from channel and matches identifiers of records to keep
	xmlSelector := func(wg *sync.WaitGroup, inp <-chan Extract, out chan<- Extract) {

		// report when this selector has no more records to process
		defer wg.Done()

		// read partitioned XML from producer channel
		for ext := range inp {

			text := ext.Text

			found := false

			FindIdentifiers(text[:], parent, find,
				func(id string) {
					id = SortStringByWords(id)
					_, ok := order[id]
					if ok {
						found = true
					}
				})

			if !found {
				// identifier field not found or not in identifier list, send empty placeholder for unshuffler
				out <- Extract{ext.Index, "", "", nil}
				continue
			}

			// send selected record
			out <- Extract{ext.Index, "", text, nil}
		}
	}

	var wg sync.WaitGroup

	// launch multiple selector goroutines
	for i := 0; i < NumServe; i++ {
		wg.Add(1)
		go xmlSelector(&wg, inp, out)
	}

	// launch separate anonymous goroutine to wait until all selectors are done
	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

// XML VALIDATION AND FORMATTING FUNCTIONS

// StreamBlocks -> StreamTokens -> ProcessStream

// ProcessTokens shows individual tokens in stream (undocumented)
func ProcessTokens(rdr <-chan string) {

	if rdr == nil {
		return
	}

	tknq := CreateTokenizer(rdr)

	if tknq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create debug tokenizer\n")
		os.Exit(1)
	}

	var buffer strings.Builder

	count := 0
	indent := 0

	for tkn := range tknq {

		tag := tkn.Tag
		name := tkn.Name
		attr := tkn.Attr

		switch tag {
		case STARTTAG:
			buffer.WriteString("ST: ")
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
			if attr != "" {
				buffer.WriteString("AT: ")
				for i := 0; i < indent; i++ {
					buffer.WriteString("  ")
				}
				buffer.WriteString(attr)
				buffer.WriteString("\n")
			}
			indent++
		case SELFTAG:
			buffer.WriteString("SL: ")
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("/")
			buffer.WriteString("\n")
			if attr != "" {
				buffer.WriteString("AT: ")
				for i := 0; i < indent; i++ {
					buffer.WriteString("  ")
				}
				buffer.WriteString(attr)
				buffer.WriteString("\n")
			}
		case STOPTAG:
			indent--
			buffer.WriteString("SP: ")
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("/")
			buffer.WriteString("\n")
		case CONTENTTAG:
			ctype := tkn.Cont
			if (ctype & LFTSPACE) != 0 {
				if (ctype & RGTSPACE) != 0 {
					buffer.WriteString("FL: ")
				} else {
					buffer.WriteString("LF: ")
				}
			} else if (ctype & RGTSPACE) != 0 {
				buffer.WriteString("RT: ")
			} else {
				buffer.WriteString("VL: ")
			}
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case CDATATAG:
			buffer.WriteString("CD: ")
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case COMMENTTAG:
			buffer.WriteString("CO: ")
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case DOCTYPETAG:
			buffer.WriteString("DC: ")
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case NOTAG:
			buffer.WriteString("NO:")
			if indent != 0 {
				buffer.WriteString(" (indent ")
				buffer.WriteString(strconv.Itoa(indent))
				buffer.WriteString(")")
			}
			buffer.WriteString("\n")
		case ISCLOSED:
			buffer.WriteString("CL:")
			if indent != 0 {
				buffer.WriteString(" (indent ")
				buffer.WriteString(strconv.Itoa(indent))
				buffer.WriteString(")")
			}
			buffer.WriteString("\n")
			txt := buffer.String()
			if txt != "" {
				// print final buffer
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			return
		default:
			buffer.WriteString("UNKONWN:")
			if indent != 0 {
				buffer.WriteString(" (indent ")
				buffer.WriteString(strconv.Itoa(indent))
				buffer.WriteString(")")
			}
			buffer.WriteString("\n")
		}

		count++
		if count > 1000 {
			count = 0
			txt := buffer.String()
			if txt != "" {
				// print current buffered output
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			buffer.Reset()
		}
	}
}

// ProcessFormat reformats XML for ease of reading
func ProcessFormat(rdr <-chan string, args []string, useTimer bool) int {

	if rdr == nil || args == nil {
		return 0
	}

	var buffer strings.Builder
	count := 0
	maxLine := 0

	// skip past command name
	args = args[1:]

	copyRecrd := false
	compRecrd := false
	flushLeft := false
	wrapAttrs := false
	ret := "\n"

	xml := ""
	customDoctype := false
	doctype := ""

	// look for [copy|compact|flush|indent|expand] specification
	if len(args) > 0 {
		inSwitch := true

		switch args[0] {
		case "compact", "compacted", "compress", "compressed", "terse", "*":
			// compress to one record per line
			compRecrd = true
			ret = ""
		case "flush", "flushed", "left":
			// suppress line indentation
			flushLeft = true
		case "expand", "expanded", "extend", "extended", "verbose", "@":
			// each attribute on its own line
			wrapAttrs = true
		case "indent", "indented", "normal", "default":
			// default behavior
		case "copy":
			// fast block copy
			copyRecrd = true
		default:
			// if not any of the controls, will check later for -xml and -doctype arguments
			inSwitch = false
		}

		if inSwitch {
			// skip past first argument
			args = args[1:]
		}
	}

	// fast block copy, supporting only -spaces processing flag
	if copyRecrd {

		for str := range rdr {
			if str == "" {
				break
			}

			os.Stdout.WriteString(str)
		}
		os.Stdout.WriteString("\n")
		return 0
	}

	unicodePolicy := ""
	scriptPolicy := ""
	mathmlPolicy := ""

	fuseTopSets := true
	keepEmptySelfClosing := false

	// look for -xml and -doctype arguments (undocumented)
	for len(args) > 0 {

		switch args[0] {
		case "-xml":
			args = args[1:]
			// -xml argument must be followed by value to use in xml line
			if len(args) < 1 || strings.HasPrefix(args[0], "-") {
				fmt.Fprintf(os.Stderr, "\nERROR: -xml argument is missing\n")
				os.Exit(1)
			}
			xml = args[0]
			args = args[1:]
		case "-doctype":
			customDoctype = true
			args = args[1:]
			if len(args) > 0 && !strings.HasPrefix(args[0], "-") {
				// if -doctype argument followed by value, use instead of DOCTYPE line
				doctype = args[0]
				args = args[1:]
			}

		// allow setting of unicode, script, and mathml flags within -format
		case "-unicode":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Unicode argument is missing\n")
				os.Exit(1)
			}
			unicodePolicy = args[1]
			args = args[2:]
		case "-script":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Script argument is missing\n")
				os.Exit(1)
			}
			scriptPolicy = args[1]
			args = args[2:]
		case "-mathml":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: MathML argument is missing\n")
				os.Exit(1)
			}
			mathmlPolicy = args[1]
			args = args[2:]

		// also allow setting additional processing flags within -format (undocumented)
		case "-strict":
			// can set -strict within -format
			DoStrict = true
			args = args[1:]
		case "-mixed":
			// can set -mixed within -format
			DoMixed = true
			args = args[1:]
		case "-compress", "-compressed":
			DoCompress = true
			args = args[1:]
		case "-accent":
			DeAccent = true
			args = args[1:]
		case "-ascii":
			DoASCII = true
			args = args[1:]
		case "-separate", "-separated":
			fuseTopSets = false
			args = args[1:]
		case "-self", "-self-closing":
			keepEmptySelfClosing = true
			args = args[1:]
		default:
			fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized option after -format command\n")
			os.Exit(1)
		}
	}

	UnicodeFix = ParseMarkup(unicodePolicy, "-unicode")
	ScriptFix = ParseMarkup(scriptPolicy, "-script")
	MathMLFix = ParseMarkup(mathmlPolicy, "-mathml")

	if UnicodeFix != NOMARKUP {
		DoUnicode = true
	}

	if ScriptFix != NOMARKUP {
		DoScript = true
	}

	if MathMLFix != NOMARKUP {
		DoMathML = true
	}

	CountLines = DoMixed || useTimer
	AllowEmbed = DoStrict || DoMixed
	ContentMods = AllowEmbed || DoCompress || DoUnicode || DoScript || DoMathML || DeAccent || DoASCII

	// array to speed up indentation
	indentSpaces := []string{
		"",
		"  ",
		"    ",
		"      ",
		"        ",
		"          ",
		"            ",
		"              ",
		"                ",
		"                  ",
	}

	indent := 0

	// indent a specified number of spaces
	doIndent := func(indt int) {
		if compRecrd || flushLeft {
			return
		}
		i := indt
		for i > 9 {
			buffer.WriteString("                    ")
			i -= 10
		}
		if i < 0 {
			return
		}
		buffer.WriteString(indentSpaces[i])
	}

	badAttributeSpacing := func(attr string) bool {

		if len(attr) < 2 {
			return false
		}

		var prev rune

		for _, ch := range attr {
			if ch == '=' && prev == ' ' {
				return true
			}
			if ch == ' ' && prev == '=' {
				return true
			}
			prev = ch
		}

		return false
	}

	// print attributes
	printAttributes := func(attr string) {

		if attr == "" {
			return
		}
		attr = strings.TrimSpace(attr)
		attr = CompressRunsOfSpaces(attr)

		if DeAccent {
			if IsNotASCII(attr) {
				attr = DoAccentTransform(attr)
			}
		}
		if DoASCII {
			if IsNotASCII(attr) {
				attr = UnicodeToASCII(attr)
			}
		}

		if wrapAttrs {

			start := 0
			idx := 0
			inQuote := false

			attlen := len(attr)

			for idx < attlen {
				ch := attr[idx]
				if ch == '=' && !inQuote {
					inQuote = true
					str := strings.TrimSpace(attr[start:idx])
					buffer.WriteString("\n")
					doIndent(indent)
					buffer.WriteString(" ")
					buffer.WriteString(str)
					// skip past equal sign
					idx++
					ch = attr[idx]
					if ch != '"' && ch != '\'' {
						// "
						// skip past unexpected blanks
						for InBlank[ch] {
							idx++
							ch = attr[idx]
						}
					}
					// skip past leading double quote
					idx++
					start = idx
				} else if ch == '"' || ch == '\'' {
					// "
					inQuote = !inQuote
					str := strings.TrimSpace(attr[start:idx])
					buffer.WriteString("=\"")
					buffer.WriteString(str)
					buffer.WriteString("\"")
					// skip past trailing double quote and (possible) space
					idx += 2
					start = idx
				} else {
					idx++
				}
			}

			buffer.WriteString("\n")
			doIndent(indent)

		} else if badAttributeSpacing(attr) {

			buffer.WriteString(" ")

			start := 0
			idx := 0

			attlen := len(attr)

			for idx < attlen {
				ch := attr[idx]
				if ch == '=' {
					str := strings.TrimSpace(attr[start:idx])
					buffer.WriteString(str)
					// skip past equal sign
					idx++
					ch = attr[idx]
					if ch != '"' && ch != '\'' {
						// "
						// skip past unexpected blanks
						for InBlank[ch] {
							idx++
							ch = attr[idx]
						}
					}
					// skip past leading double quote
					idx++
					start = idx
				} else if ch == '"' || ch == '\'' {
					// "
					str := strings.TrimSpace(attr[start:idx])
					buffer.WriteString("=\"")
					buffer.WriteString(str)
					buffer.WriteString("\"")
					// skip past trailing double quote and (possible) space
					idx += 2
					start = idx
				} else {
					idx++
				}
			}

		} else {

			buffer.WriteString(" ")
			buffer.WriteString(attr)
		}
	}

	parent := ""
	pfx := ""
	skip := 0
	okIndent := true

	printXMLAndDoctype := func(xml, doctype, parent string) {

		// check for xml line explicitly set in argument
		if xml != "" {
			xml = strings.TrimSpace(xml)
			if strings.HasPrefix(xml, "<") {
				xml = xml[1:]
			}
			if strings.HasPrefix(xml, "?") {
				xml = xml[1:]
			}
			if strings.HasPrefix(xml, "xml") {
				xml = xml[3:]
			}
			if strings.HasPrefix(xml, " ") {
				xml = xml[1:]
			}
			if strings.HasSuffix(xml, "?>") {
				xlen := len(xml)
				xml = xml[:xlen-2]
			}
			xml = strings.TrimSpace(xml)

			buffer.WriteString("<?xml ")
			buffer.WriteString(xml)
			buffer.WriteString("?>")
		} else {
			buffer.WriteString("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
		}

		buffer.WriteString("\n")

		// check for doctype taken from XML file or explicitly set in argument
		if doctype != "" {
			doctype = strings.TrimSpace(doctype)
			if strings.HasPrefix(doctype, "<") {
				doctype = doctype[1:]
			}
			if strings.HasPrefix(doctype, "!") {
				doctype = doctype[1:]
			}
			if strings.HasPrefix(doctype, "DOCTYPE") {
				doctype = doctype[7:]
			}
			if strings.HasPrefix(doctype, " ") {
				doctype = doctype[1:]
			}
			doctype = strings.TrimSuffix(doctype, ">")
			doctype = strings.TrimSpace(doctype)

			buffer.WriteString("<!DOCTYPE ")
			buffer.WriteString(doctype)
			buffer.WriteString(">")
		} else {
			buffer.WriteString("<!DOCTYPE ")
			buffer.WriteString(parent)
			buffer.WriteString(">")
		}

		buffer.WriteString("\n")
	}

	cleanupMixed := func(txt string) string {

		txt = DoTrimFlankingHTML(txt)
		if HasBadSpace(txt) {
			txt = CleanupBadSpaces(txt)
		}
		if HasAdjacentSpaces(txt) {
			txt = CompressRunsOfSpaces(txt)
		}
		if NeedsTightening(txt) {
			txt = TightenParentheses(txt)
		}

		return txt
	}

	doCleanup := func(tkn Token, nxtTag TagType, nxtName, nxtAttr string) {

		if skip > 0 {
			skip--
			return
		}

		name := tkn.Name

		switch tkn.Tag {
		case STARTTAG:
			// detect first start tag, print xml and doctype parent
			if indent == 0 && parent == "" {
				parent = name
				printXMLAndDoctype(xml, doctype, parent)
				// do not fuse <opt> or <anon> top-level objects (converted from JSON)
				if parent == "opt" || parent == "anon" {
					fuseTopSets = false
				}
			}
			// convert start-stop to self-closing tag if attributes are present, otherwise skip
			if nxtTag == STOPTAG && nxtName == name {
				if tkn.Attr != "" || keepEmptySelfClosing {
					buffer.WriteString(pfx)
					doIndent(indent)
					buffer.WriteString("<")
					buffer.WriteString(name)
					printAttributes(tkn.Attr)
					buffer.WriteString("/>")
					pfx = ret
					okIndent = true
				}
				skip++
				return
			}
			buffer.WriteString(pfx)
			doIndent(indent)
			indent++
			buffer.WriteString("<")
			buffer.WriteString(name)
			printAttributes(tkn.Attr)
			buffer.WriteString(">")
			pfx = ret
			okIndent = true
			if compRecrd && indent == 1 {
				buffer.WriteString("\n")
			}
		case SELFTAG:
			if tkn.Attr != "" || keepEmptySelfClosing {
				buffer.WriteString(pfx)
				doIndent(indent)
				buffer.WriteString("<")
				buffer.WriteString(name)
				printAttributes(tkn.Attr)
				buffer.WriteString("/>")
				pfx = ret
				okIndent = true
			}
		case STOPTAG:
			// skip internal copies of top-level </parent><parent> tags (to fuse multiple chunks returned by efetch)
			// do not skip if attributes are present, unless pattern ends in "Set" (e.g., <DocumentSummarySet status="OK">)
			if nxtTag == STARTTAG && indent == 1 && fuseTopSets && nxtName == parent {
				if nxtAttr == "" || (strings.HasSuffix(parent, "Set") && len(parent) > 3) {
					skip++
					return
				}
			}
			buffer.WriteString(pfx)
			indent--
			if okIndent {
				doIndent(indent)
			}
			buffer.WriteString("</")
			buffer.WriteString(name)
			buffer.WriteString(">")
			if DoMixed && nxtTag == CONTENTTAG {
				buffer.WriteString(" ")
			}
			pfx = ret
			okIndent = true
			if compRecrd && indent < 2 {
				buffer.WriteString("\n")
			}
		case CONTENTTAG:
			if nxtTag == STARTTAG || nxtTag == SELFTAG {
				if DoStrict {
					fmt.Fprintf(os.Stderr, "ERROR: UNRECOGNIZED MIXED CONTENT <%s> in <%s>\n", nxtName, name)
				} else if !DoMixed {
					fmt.Fprintf(os.Stderr, "ERROR: UNEXPECTED MIXED CONTENT <%s> in <%s>\n", nxtName, name)
				}
			}
			if len(name) > 0 && IsNotJustWhitespace(name) {
				// support for all content processing flags
				if DoStrict || DoMixed || DoCompress {
					ctype := tkn.Cont
					name = CleanupContents(name, (ctype&ASCII) != 0, (ctype&AMPER) != 0, (ctype&MIXED) != 0)
				}
				buffer.WriteString(name)
			}
			if DoMixed && nxtTag == STARTTAG {
				buffer.WriteString(" ")
			}
			pfx = ""
			okIndent = false
		case CDATATAG, COMMENTTAG:
			// ignore
		case DOCTYPETAG:
			if customDoctype && doctype == "" {
				doctype = name
			}
		case NOTAG:
		case ISCLOSED:
			// now handled at end of calling function
		default:
			buffer.WriteString(pfx)
			pfx = ""
			okIndent = false
		}

		count++
		if count > 1000 {
			count = 0
			txt := buffer.String()
			if DoMixed {
				txt = cleanupMixed(txt)
			}
			if txt != "" {
				// print current buffered output
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			buffer.Reset()
		}
	}

	var prev Token
	primed := false
	skipDoctype := false

	// track adjacent pairs to give look-ahead at next token
	doPair := func(tkn Token) {

		if tkn.Tag == NOTAG {
			return
		}

		maxLine = tkn.Line

		if tkn.Tag == DOCTYPETAG {
			if skipDoctype {
				return
			}
			skipDoctype = true
		}

		if primed {
			doCleanup(prev, tkn.Tag, tkn.Name, tkn.Attr)
		}

		prev = Token{tkn.Tag, tkn.Cont, tkn.Name, tkn.Attr, tkn.Index, tkn.Line}
		primed = true
	}

	ParseXML("", "", rdr, doPair, nil, nil)

	// handle isclosed tag
	if primed {
		buffer.WriteString(pfx)
		txt := buffer.String()
		if DoMixed {
			txt = cleanupMixed(txt)
		}
		if txt != "" {
			// print final buffer
			fmt.Fprintf(os.Stdout, "%s", txt)
		}
	}

	return maxLine
}

// ProcessOutline displays outline of XML structure
func ProcessOutline(rdr <-chan string) {

	if rdr == nil {
		return
	}

	tknq := CreateTokenizer(rdr)

	if tknq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create outline tokenizer\n")
		os.Exit(1)
	}

	var buffer strings.Builder

	count := 0
	indent := 0

	for tkn := range tknq {

		tag := tkn.Tag
		name := tkn.Name

		switch tag {
		case STARTTAG:
			if name == "eSummaryResult" ||
				name == "eLinkResult" ||
				name == "eInfoResult" ||
				name == "PubmedArticleSet" ||
				name == "DocumentSummarySet" ||
				name == "INSDSet" ||
				name == "Entrezgene-Set" ||
				name == "TaxaSet" {
				break
			}
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
			indent++
		case SELFTAG:
			for i := 0; i < indent; i++ {
				buffer.WriteString("  ")
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case STOPTAG:
			indent--
		case DOCTYPETAG:
		case NOTAG:
		case ISCLOSED:
			txt := buffer.String()
			if txt != "" {
				// print final buffer
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			return
		default:
		}

		count++
		if count > 1000 {
			count = 0
			txt := buffer.String()
			if txt != "" {
				// print current buffered output
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			buffer.Reset()
		}
	}
}

// ProcessSynopsis displays paths to XML elements
func ProcessSynopsis(rdr <-chan string, leaf bool, delim string) {

	if rdr == nil {
		return
	}

	tknq := CreateTokenizer(rdr)

	if tknq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create synopsis tokenizer\n")
		os.Exit(1)
	}

	var buffer strings.Builder
	count := 0

	// synopsisLevel recursive definition
	var synopsisLevel func(string) bool

	synopsisLevel = func(parent string) bool {

		for tkn := range tknq {

			tag := tkn.Tag
			name := tkn.Name

			switch tag {
			case STARTTAG:
				if name == "eSummaryResult" ||
					name == "eLinkResult" ||
					name == "eInfoResult" ||
					name == "PubmedArticleSet" ||
					name == "DocumentSummarySet" ||
					name == "INSDSet" ||
					name == "Entrezgene-Set" ||
					name == "TaxaSet" {
					break
				}
				if leaf {
					if name == "root" ||
						name == "opt" ||
						name == "anon" {
						break
					}
				}
				if !leaf {
					// show all paths, including container objects
					if parent != "" {
						buffer.WriteString(parent)
						buffer.WriteString(delim)
					}
					buffer.WriteString(name)
					buffer.WriteString("\n")
				}
				path := parent
				if path != "" {
					path += delim
				}
				path += name
				if synopsisLevel(path) {
					return true
				}
			case SELFTAG:
				if parent != "" {
					buffer.WriteString(parent)
					buffer.WriteString(delim)
				}
				buffer.WriteString(name)
				buffer.WriteString("\n")
			case STOPTAG:
				// break recursion
				return false
			case CONTENTTAG:
				if leaf {
					// only show endpoint paths
					if parent != "" {
						buffer.WriteString(parent)
						buffer.WriteString("\n")
					}
				}
			case DOCTYPETAG:
			case NOTAG:
			case ISCLOSED:
				txt := buffer.String()
				if txt != "" {
					// print final buffer
					fmt.Fprintf(os.Stdout, "%s", txt)
				}
				return true
			default:
			}

			count++
			if count > 1000 {
				count = 0
				txt := buffer.String()
				if txt != "" {
					// print current buffered output
					fmt.Fprintf(os.Stdout, "%s", txt)
				}
				buffer.Reset()
			}
		}
		return true
	}

	for {
		// may have concatenated XMLs, loop through all
		if synopsisLevel("") {
			return
		}
	}
}

// ProcessVerify checks for well-formed XML
func ProcessVerify(rdr <-chan string, args []string) int {

	if rdr == nil || args == nil {
		return 0
	}

	CountLines = true

	tknq := CreateTokenizer(rdr)

	if tknq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create validator tokenizer\n")
		os.Exit(1)
	}

	var find *Find

	// skip past command name
	args = args[1:]

	if len(args) > 0 {
		// specify record identifier (undocumented)
		find = ParseIndex(args[0])
		args = args[1:]
	}

	reportHTML := false
	if len(args) > 0 && args[0] == "-html" {
		// report encoded mixed-content tags (undocumented)
		reportHTML = true
		args = args[1:]
	}

	// report unexpectedly large maximum nesting depth (undocumented)
	maxDepth := 0
	depthLine := 0
	depthID := ""
	maxLine := 0

	// warn if HTML tags are not well-formed
	unbalancedHTML := func(text string) bool {

		var arry []string

		idx := 0
		txtlen := len(text)

		inTag := false
		start := 0
		stop := -1
		var last byte

		for idx < txtlen {
			ch := text[idx]
			if ch == '<' {
				if inTag {
					return true
				}
				inTag = true
				start = idx
				stop = -1
			} else if ch == ' ' || ch == '\n' {
				// space before attributes marks end of tag
				if stop < 0 {
					stop = idx
				}
			} else if ch == '>' {
				if !inTag {
					return true
				}
				inTag = false
				if stop < 0 {
					stop = idx
				}
				curr := text[start+1 : stop]
				if strings.HasPrefix(curr, "/") {
					curr = curr[1:]
					if len(arry) < 1 {
						return true
					}
					prev := arry[len(arry)-1]
					if curr != prev {
						return true
					}
					arry = arry[:len(arry)-1]
				} else if last == '/' {
					// ignore self-closing tag
				} else {
					arry = append(arry, curr)
				}
			}
			last = ch
			idx++
		}

		if inTag {
			return true
		}

		if len(arry) > 0 {
			return true
		}

		return false
	}

	// warn if HTML tags are encoded
	encodedHTML := func(str string) bool {

		lookAhead := func(txt string, to int) string {

			mx := len(txt)
			if to > mx {
				to = mx
			}
			pos := strings.Index(txt[:to], "gt;")
			if pos > 0 {
				to = pos + 3
			}
			return txt[:to]
		}

		for i, ch := range str {
			if ch == '<' {
				continue
			} else if ch != '&' {
				continue
			} else if strings.HasPrefix(str[i:], "&lt;") {
				sub := lookAhead(str[i:], 14)
				_, ok := htmlRepair[sub]
				if ok {
					return true
				}
			} else if strings.HasPrefix(str[i:], "&amp;lt;") {
				sub := lookAhead(str[i:], 22)
				_, ok := htmlRepair[sub]
				if ok {
					return true
				}
			} else if strings.HasPrefix(str[i:], "&amp;amp;") {
				return true
			}
		}

		return false
	}

	currID := ""

	// verifyLevel recursive definition
	var verifyLevel func(string, string, int)

	// verify integrity of XML object nesting (well-formed)
	verifyLevel = func(parent, prev string, level int) {

		status := START
		for tkn := range tknq {

			tag := tkn.Tag
			name := tkn.Name
			line := tkn.Line
			maxLine = line

			if level > maxDepth {
				maxDepth = level
				depthLine = line
				depthID = currID
			}

			switch tag {
			case STARTTAG:
				if status == CHAR && !DoMixed {
					fmt.Fprintf(os.Stdout, "%s%8d\t<%s> not expected after contents\n", currID, line, name)
				}
				verifyLevel(name, parent, level+1)
				// returns here after recursion
				status = STOP
			case SELFTAG:
				status = OTHER
			case STOPTAG:
				if parent != name && parent != "" {
					fmt.Fprintf(os.Stdout, "%s%8d\tExpected </%s>, found </%s>\n", currID, line, parent, name)
				}
				if level < 1 {
					fmt.Fprintf(os.Stdout, "%s%8d\tUnexpected </%s> at end of XML\n", currID, line, name)
				}
				// break recursion
				return
			case CONTENTTAG:
				// check for content index match
				if find != nil && find.Index != "" {
					if parent == find.Match || find.Match == "" {
						if find.Parent == "" || prev == find.Parent {
							currID = name + "\t"
						}
					}
				}
				if status != START && !DoMixed {
					fmt.Fprintf(os.Stdout, "%s%8d\tContents not expected before </%s>\n", currID, line, parent)
				}
				if AllowEmbed {
					if unbalancedHTML(name) {
						fmt.Fprintf(os.Stdout, "%s%8d\tUnbalanced mixed-content tags in <%s>\n", currID, line, parent)
					}
					if reportHTML && encodedHTML(name) {
						fmt.Fprintf(os.Stdout, "%s%8d\tEncoded mixed-content markup in <%s>\n", currID, line, parent)
					}
				}
				status = CHAR
			case CDATATAG, COMMENTTAG:
				status = OTHER
			case DOCTYPETAG:
			case NOTAG:
			case ISCLOSED:
				if level > 0 {
					fmt.Fprintf(os.Stdout, "%s%8d\tUnexpected end of data\n", currID, line)
				}
				return
			default:
				status = OTHER
			}
		}
	}

	verifyLevel("", "", 0)

	if maxDepth > 20 {
		fmt.Fprintf(os.Stdout, "%s%8d\tMaximum nesting, %d levels\n", depthID, depthLine, maxDepth)
	}

	return maxLine
}

// ProcessFilter modifies XML content, comments, or CDATA
func ProcessFilter(rdr <-chan string, args []string) {

	if rdr == nil || args == nil {
		return
	}

	tknq := CreateTokenizer(rdr)

	if tknq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create filter tokenizer\n")
		os.Exit(1)
	}

	var buffer strings.Builder

	count := 0

	// skip past command name
	args = args[1:]

	max := len(args)
	if max < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to xtract -filter\n")
		os.Exit(1)
	}

	pttrn := args[0]

	args = args[1:]
	max--

	if max < 2 {
		fmt.Fprintf(os.Stderr, "\nERROR: No object name supplied to xtract -filter\n")
		os.Exit(1)
	}

	type ActionType int

	const (
		NOACTION ActionType = iota
		DORETAIN
		DOREMOVE
		DOENCODE
		DODECODE
		DOSHRINK
		DOEXPAND
		DOACCENT
	)

	action := args[0]

	what := NOACTION
	switch action {
	case "retain":
		what = DORETAIN
	case "remove":
		what = DOREMOVE
	case "encode":
		what = DOENCODE
	case "decode":
		what = DODECODE
	case "shrink":
		what = DOSHRINK
	case "expand":
		what = DOEXPAND
	case "accent":
		what = DOACCENT
	default:
		fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized action '%s' supplied to xtract -filter\n", action)
		os.Exit(1)
	}

	trget := args[1]

	which := NOTAG
	switch trget {
	case "attribute", "attributes":
		which = ATTRIBTAG
	case "content", "contents":
		which = CONTENTTAG
	case "cdata", "CDATA":
		which = CDATATAG
	case "comment", "comments":
		which = COMMENTTAG
	case "object":
		// object normally retained
		which = OBJECTTAG
	case "container":
		which = CONTAINERTAG
	default:
		fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized target '%s' supplied to xtract -filter\n", trget)
		os.Exit(1)
	}

	inPattern := false
	prevName := ""

	for tkn := range tknq {

		tag := tkn.Tag
		name := tkn.Name
		attr := tkn.Attr

		switch tag {
		case STARTTAG:
			prevName = name
			if name == pttrn {
				inPattern = true
				if which == CONTAINERTAG && what == DOREMOVE {
					continue
				}
			}
			if inPattern && which == OBJECTTAG && what == DOREMOVE {
				continue
			}
			buffer.WriteString("<")
			buffer.WriteString(name)
			if attr != "" {
				if which != ATTRIBTAG || what != DOREMOVE {
					attr = strings.TrimSpace(attr)
					attr = CompressRunsOfSpaces(attr)
					buffer.WriteString(" ")
					buffer.WriteString(attr)
				}
			}
			buffer.WriteString(">\n")
		case SELFTAG:
			if inPattern && which == OBJECTTAG && what == DOREMOVE {
				continue
			}
			buffer.WriteString("<")
			buffer.WriteString(name)
			if attr != "" {
				if which != ATTRIBTAG || what != DOREMOVE {
					attr = strings.TrimSpace(attr)
					attr = CompressRunsOfSpaces(attr)
					buffer.WriteString(" ")
					buffer.WriteString(attr)
				}
			}
			buffer.WriteString("/>\n")
		case STOPTAG:
			if name == pttrn {
				inPattern = false
				if which == OBJECTTAG && what == DOREMOVE {
					continue
				}
				if which == CONTAINERTAG && what == DOREMOVE {
					continue
				}
			}
			if inPattern && which == OBJECTTAG && what == DOREMOVE {
				continue
			}
			buffer.WriteString("</")
			buffer.WriteString(name)
			buffer.WriteString(">\n")
		case CONTENTTAG:
			if inPattern && which == OBJECTTAG && what == DOREMOVE {
				continue
			}
			if inPattern && which == CONTENTTAG && what == DOEXPAND {
				var words []string
				if strings.Contains(name, "|") {
					words = strings.FieldsFunc(name, func(c rune) bool {
						return c == '|'
					})
				} else if strings.Contains(name, ",") {
					words = strings.FieldsFunc(name, func(c rune) bool {
						return c == ','
					})
				} else {
					words = strings.Fields(name)
				}
				between := ""
				for _, item := range words {
					max := len(item)
					for max > 1 {
						ch := item[max-1]
						if ch != '.' && ch != ',' && ch != ':' && ch != ';' {
							break
						}
						// trim trailing punctuation
						item = item[:max-1]
						// continue checking for runs of punctuation at end
						max--
					}
					if HasFlankingSpace(item) {
						item = strings.TrimSpace(item)
					}
					if item != "" {
						if between != "" {
							buffer.WriteString(between)
						}
						buffer.WriteString(item)
						buffer.WriteString("\n")
						between = "</" + prevName + ">\n<" + prevName + ">\n"
					}
				}
				continue
			}
			if inPattern && which == tag {
				switch what {
				case DORETAIN:
					// default behavior for content - can use -filter X retain content as a no-op
				case DOREMOVE:
					continue
				case DOENCODE:
					name = html.EscapeString(name)
				case DODECODE:
					name = html.UnescapeString(name)
				case DOSHRINK:
					name = CompressRunsOfSpaces(name)
				case DOACCENT:
					if IsNotASCII(name) {
						name = DoAccentTransform(name)
					}
				default:
					continue
				}
			}
			// content normally printed
			if HasFlankingSpace(name) {
				name = strings.TrimSpace(name)
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case CDATATAG:
			if inPattern && which == OBJECTTAG && what == DOREMOVE {
				continue
			}
			if inPattern && which == tag {
				switch what {
				case DORETAIN:
					// cdata requires explicit retain command
				case DOREMOVE:
					continue
				case DOENCODE:
					name = html.EscapeString(name)
				case DODECODE:
					name = html.UnescapeString(name)
				case DOSHRINK:
					name = CompressRunsOfSpaces(name)
				case DOACCENT:
					if IsNotASCII(name) {
						name = DoAccentTransform(name)
					}
				default:
					continue
				}
				// cdata normally removed
				if HasFlankingSpace(name) {
					name = strings.TrimSpace(name)
				}
				buffer.WriteString(name)
				buffer.WriteString("\n")
			}
		case COMMENTTAG:
			if inPattern && which == OBJECTTAG && what == DOREMOVE {
				continue
			}
			if inPattern && which == tag {
				switch what {
				case DORETAIN:
					// comment requires explicit retain command
				case DOREMOVE:
					continue
				case DOENCODE:
					name = html.EscapeString(name)
				case DODECODE:
					name = html.UnescapeString(name)
				case DOSHRINK:
					name = CompressRunsOfSpaces(name)
				case DOACCENT:
					if IsNotASCII(name) {
						name = DoAccentTransform(name)
					}
				default:
					continue
				}
				// comment normally removed
				if HasFlankingSpace(name) {
					name = strings.TrimSpace(name)
				}
				buffer.WriteString(name)
				buffer.WriteString("\n")
			}
		case DOCTYPETAG:
		case NOTAG:
		case ISCLOSED:
			txt := buffer.String()
			if txt != "" {
				// print final buffer
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			return
		default:
		}

		count++
		if count > 1000 {
			count = 0
			txt := buffer.String()
			if txt != "" {
				// print current buffered output
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			buffer.Reset()
		}
	}
}

// ProcessNormalize adjusts XML fields to conform to common conventions
func ProcessNormalize(rdr <-chan string, args []string) {

	if rdr == nil || args == nil {
		return
	}

	tknq := CreateTokenizer(rdr)

	if tknq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create normalize tokenizer\n")
		os.Exit(1)
	}

	var buffer strings.Builder

	count := 0

	// e.g., xtract -normalize pubmed

	// skip past command name
	args = args[1:]

	max := len(args)
	if max < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: No database name supplied to xtract -normalize\n")
		os.Exit(1)
	}

	db := args[0]

	// force -strict cleanup flag
	switch db {
	case "bioc", "biocollections", "clinvar", "dbvar", "gap", "gapplus", "grasp", "pccompound", "pcsubstance":
	default:
		DoStrict = true
	}
	AllowEmbed = true
	ContentMods = true

	uid := ""
	isDocsum := false
	prevName := ""

	// removes mixed content tags
	mfix := strings.NewReplacer(
		"<b>", "",
		"<i>", "",
		"<u>", "",
		"</b>", "",
		"</i>", "",
		"</u>", "",
		"<b/>", "",
		"<i/>", "",
		"<u/>", "",
		"<sup>", "",
		"<sub>", "",
		"</sup>", "",
		"</sub>", "",
		"<sup/>", "",
		"<sub/>", "",
	)

	// reencodes < and > to &lt and &gt
	rfix := strings.NewReplacer(
		"<", "&lt;",
		">", "&gt;",
	)

	for tkn := range tknq {

		tag := tkn.Tag
		name := tkn.Name
		attr := tkn.Attr

		switch tag {
		case STARTTAG:
			if name == "Id" && uid != "" {
				uid = ""
			}
			if uid != "" {
				// if object after DocumentSummary is not already Id, create Id from rescued attribute
				buffer.WriteString("<Id>\n")
				buffer.WriteString(uid)
				buffer.WriteString("</Id>\n")
				// clear until next docsum
				uid = ""
			}
			if name == "DocumentSummary" {
				isDocsum = true
				if strings.HasPrefix(attr, "uid=\"") && strings.HasSuffix(attr, "\"") {
					attr = strings.TrimPrefix(attr, "uid=\"")
					attr = strings.TrimSuffix(attr, "\"")
					// store uid from DocumentSummary
					uid = attr
					// remove attribute
					attr = ""
				}
			}
			buffer.WriteString("<")
			buffer.WriteString(name)
			if attr != "" {
				attr = strings.TrimSpace(attr)
				attr = CompressRunsOfSpaces(attr)
				buffer.WriteString(" ")
				buffer.WriteString(attr)
			}
			buffer.WriteString(">\n")
			prevName = name
		case SELFTAG:
			buffer.WriteString("<")
			buffer.WriteString(name)
			if attr != "" {
				attr = strings.TrimSpace(attr)
				attr = CompressRunsOfSpaces(attr)
				buffer.WriteString(" ")
				buffer.WriteString(attr)
			}
			buffer.WriteString("/>\n")
		case STOPTAG:
			buffer.WriteString("</")
			buffer.WriteString(name)
			buffer.WriteString(">\n")
		case CONTENTTAG:
			if isDocsum {
				if db == "pubmed" && prevName == "Title" {
					if strings.Contains(name, "&") ||
						strings.Contains(name, "<") ||
						strings.Contains(name, ">") {
						ctype := tkn.Cont
						name = CleanupContents(name, (ctype&ASCII) != 0, (ctype&AMPER) != 0, (ctype&MIXED) != 0)
						if HasFlankingSpace(name) {
							name = strings.TrimSpace(name)
						}
						name = html.UnescapeString(name)
						// remove mixed content tags
						name = mfix.Replace(name)
						// reencode < and > to avoid breaking XML
						if strings.Contains(name, "<") || strings.Contains(name, ">") {
							name = rfix.Replace(name)
						}
					}
				} else if db == "gene" && prevName == "Summary" {
					if strings.Contains(name, "&amp;") {
						if HasFlankingSpace(name) {
							name = strings.TrimSpace(name)
						}
						name = html.UnescapeString(name)
						// reencode < and > to avoid breaking XML
						if strings.Contains(name, "<") || strings.Contains(name, ">") {
							name = rfix.Replace(name)
						}
					}
				} else if (db == "biosample" && prevName == "SampleData") ||
					(db == "medgen" && prevName == "ConceptMeta") ||
					(db == "sra" && prevName == "ExpXml") ||
					(db == "sra" && prevName == "Runs") {
					if strings.Contains(name, "&lt;") && strings.Contains(name, "&gt;") {
						if HasFlankingSpace(name) {
							name = strings.TrimSpace(name)
						}
						name = html.UnescapeString(name)
					}
				}
			} else {
				if db == "pubmed" {
					ctype := tkn.Cont
					name = CleanupContents(name, (ctype&ASCII) != 0, (ctype&AMPER) != 0, (ctype&MIXED) != 0)
					if HasFlankingSpace(name) {
						name = strings.TrimSpace(name)
					}
				} else if db == "bioc" {
					name = CleanupContents(name, true, true, true)
					if HasFlankingSpace(name) {
						name = strings.TrimSpace(name)
					}
				}
			}
			// content normally printed
			if HasFlankingSpace(name) {
				name = strings.TrimSpace(name)
			}
			buffer.WriteString(name)
			buffer.WriteString("\n")
		case CDATATAG:
			if isDocsum {
				if db == "assembly" && prevName == "Meta" {
					if strings.Contains(name, "<") && strings.Contains(name, ">") {
						// if CDATA contains embedded XML, simply remove CDATA wrapper
						if HasFlankingSpace(name) {
							name = strings.TrimSpace(name)
						}
						buffer.WriteString(name)
						buffer.WriteString("\n")
					}
				} else if db == "gtr" && prevName == "Extra" {
					// remove entire CDATA contents
				}
			}
		case COMMENTTAG:
			if !isDocsum {
				if db == "sra" {
					if strings.Contains(name, "<") && strings.Contains(name, ">") {
						// if comment contains embedded XML, remove comment wrapper and trim to leading < bracket
						pos := strings.Index(name, "<")
						if pos > 0 {
							name = name[pos:]
						}
						if HasFlankingSpace(name) {
							name = strings.TrimSpace(name)
						}
						buffer.WriteString(name)
						buffer.WriteString("\n")
					}
				}
			}
		case DOCTYPETAG:
			doctype := strings.TrimSpace(name)
			if strings.HasPrefix(doctype, "<") {
				doctype = doctype[1:]
			}
			if strings.HasPrefix(doctype, "!") {
				doctype = doctype[1:]
			}
			if strings.HasPrefix(doctype, "DOCTYPE") {
				doctype = doctype[7:]
			}
			if strings.HasPrefix(doctype, " ") {
				doctype = doctype[1:]
			}
			doctype = strings.TrimSuffix(doctype, ">")
			doctype = strings.TrimSpace(doctype)

			buffer.WriteString("<!DOCTYPE ")
			buffer.WriteString(doctype)
			buffer.WriteString(">")
		case NOTAG:
		case ISCLOSED:
			txt := buffer.String()
			if txt != "" {
				// print final buffer
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			return
		default:
		}

		count++
		if count > 1000 {
			count = 0
			txt := buffer.String()
			if txt != "" {
				// print current buffered output
				fmt.Fprintf(os.Stdout, "%s", txt)
			}
			buffer.Reset()
		}
	}
}

// JSONTokenizer sends sequential JSON tokens down a channel
func JSONTokenizer(inp io.Reader) <-chan string {

	if inp == nil {
		return nil
	}

	out := make(chan string, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create JSON tokenizer channel\n")
		os.Exit(1)
	}

	tokenizeJSON := func(inp io.Reader, out chan<- string) {

		// close channel when all tokens have been sent
		defer close(out)

		// use token decoder from encoding/json package
		dec := json.NewDecoder(inp)
		if dec == nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to create JSON Decoder\n")
			os.Exit(1)
		}
		dec.UseNumber()

		for {
			t, err := dec.Token()
			if err == io.EOF {
				return
			}
			if err != nil {
				fmt.Fprintf(os.Stderr, "\nERROR: Unable to read JSON token '%s'\n", err)
				os.Exit(1)
			}

			// type switch performs sequential type assertions until match is found
			switch v := t.(type) {
			case json.Delim:
				// opening or closing braces (for objects) or brackets (for arrays)
				out <- string(v)
			case string:
				str := v
				if HasAdjacentSpacesOrNewline(str) {
					str = CompressRunsOfSpaces(str)
				}
				out <- str
			case json.Number:
				out <- v.String()
			case float64:
				out <- strconv.FormatFloat(v, 'f', -1, 64)
			case bool:
				if v {
					out <- "true"
				} else {
					out <- "false"
				}
			case nil:
				out <- "null"
			default:
				out <- t.(string)
			}
		}
	}

	// launch single tokenizer goroutine
	go tokenizeJSON(inp, out)

	return out
}

// JSONConverter parses JSON token stream into XML object stream
func JSONConverter(inp <-chan string, set, rec, nest string) <-chan string {

	if inp == nil {
		return nil
	}

	out := make(chan string, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create JSON converter channel\n")
		os.Exit(1)
	}

	// opt is used for anonymous top-level objects, anon for anonymous top-level arrays
	opt := "opt"
	anon := "anon"
	if rec != "" {
		// override record delimiter
		opt = rec
		anon = rec
	}

	flat := false
	plural := false
	depth := false

	switch nest {
	case "flat":
		flat = true
	case "plural", "name":
		plural = true
	case "depth", "deep", "level":
		depth = true
	}

	// convertJSON sends XML records down a channel
	convertJSON := func(inp <-chan string, out chan<- string) {

		// close channel when all tokens have been processed
		defer close(out)

		// ensure that XML tags are legal (initial digit allowed by xtract for biological data in JSON)
		fixTag := func(tag string) string {

			if tag == "" {
				return tag
			}

			okay := true
			for _, ch := range tag {
				if !InElement[ch] {
					okay = false
				}
			}
			if okay {
				return tag
			}

			var temp strings.Builder

			// replace illegal characters with underscore
			for _, ch := range tag {
				if InElement[ch] {
					temp.WriteRune(ch)
				} else {
					temp.WriteRune('_')
				}
			}

			return temp.String()
		}

		// closure silently places local variable pointer onto inner function call stack
		var buffer strings.Builder

		// array to speed up indentation
		indentSpaces := []string{
			"",
			"  ",
			"    ",
			"      ",
			"        ",
			"          ",
			"            ",
			"              ",
			"                ",
			"                  ",
		}

		indent := 0
		if set != "" {
			indent = 1
		}

		// indent a specified number of spaces
		doIndent := func(indt int) {
			i := indt
			for i > 9 {
				buffer.WriteString("                    ")
				i -= 10
			}
			if i < 0 {
				return
			}
			buffer.WriteString(indentSpaces[i])
		}

		// recursive function definitions
		var parseObject func(tag string)
		var parseArray func(tag, pfx string, lvl int)

		// recursive descent parser uses mutual recursion
		parseValue := func(tag, pfx, tkn string, lvl int) {

			switch tkn {
			case "{":
				parseObject(tag)
				// no break needed, would use fallthrough to explicitly cause program control to flow to the next case
			case "[":
				if flat {
					parseArray(tag, pfx, lvl+1)
				} else if lvl > 0 {
					// nested JSON arrays create recursive XML objects
					doIndent(indent)
					indent++
					tg := tag
					if plural {
						tg = inflector.Pluralize(tag)
					}
					buffer.WriteString("<")
					buffer.WriteString(tg)
					buffer.WriteString(">\n")
					if depth {
						parseArray(pfx+"_"+strconv.Itoa(lvl), tag, lvl+1)
					} else {
						parseArray(tag, pfx, lvl+1)
					}
					indent--
					doIndent(indent)
					buffer.WriteString("</")
					buffer.WriteString(tg)
					buffer.WriteString(">\n")
				} else {
					parseArray(tag, pfx, lvl+1)
				}
			case "}", "]":
				// should not get here, decoder tracks nesting of braces and brackets
			case "":
				// empty value string generates self-closing object
				doIndent(indent)
				buffer.WriteString("<")
				buffer.WriteString(tag)
				buffer.WriteString("/>\n")
			default:
				// write object and contents to string builder
				doIndent(indent)
				tkn = strings.TrimSpace(tkn)
				tkn = html.EscapeString(tkn)
				buffer.WriteString("<")
				buffer.WriteString(tag)
				buffer.WriteString(">")
				buffer.WriteString(tkn)
				buffer.WriteString("</")
				buffer.WriteString(tag)
				buffer.WriteString(">\n")
			}
		}

		parseObject = func(tag string) {

			doIndent(indent)
			indent++
			buffer.WriteString("<")
			buffer.WriteString(tag)
			buffer.WriteString(">\n")

			for {
				// shadowing tag variable inside for loop does not step on value of tag argument in outer scope
				tag, ok := <-inp
				if !ok {
					break
				}

				if tag == "}" || tag == "]" {
					break
				}

				tag = fixTag(tag)

				tkn, ok := <-inp
				if !ok {
					break
				}

				if tkn == "}" || tkn == "]" {
					break
				}

				parseValue(tag, tag, tkn, 0)
			}

			indent--
			doIndent(indent)
			buffer.WriteString("</")
			buffer.WriteString(tag)
			buffer.WriteString(">\n")
		}

		parseArray = func(tag, pfx string, lvl int) {

			for {
				tkn, ok := <-inp
				if !ok {
					break
				}

				if tkn == "}" || tkn == "]" {
					break
				}

				parseValue(tag, pfx, tkn, lvl)
			}
		}

		// process stream of catenated top-level JSON objects or arrays
		for {
			tkn, ok := <-inp
			if !ok {
				break
			}
			if tkn == "{" {
				parseObject(opt)
			} else if tkn == "[" {
				parseArray(anon, anon, 0)
			} else {
				break
			}

			txt := buffer.String()

			// send result through output channel
			out <- txt

			buffer.Reset()

			runtime.Gosched()
		}
	}

	// launch single converter goroutine
	go convertJSON(inp, out)

	return out
}

// READ TAB-DELIMITED FILE AND WRAP IN XML FIELDS

// TableConverter parses tab-delimited (-t2x) or comma-separated values (-c2x) files into XML
func TableConverter(inp io.Reader, delim string, args []string) int {

	// e.g., xtract -t2x -set Set -rec Rec -skip 0 Uid Name

	if inp == nil {
		return 0
	}

	cmmd := args[0]
	args = args[1:]

	head := ""
	tail := ""

	hd := ""
	tl := ""

	skip := 0
	lower := false
	upper := false
	indent := true

	var fields []string
	numFlds := 0

	for len(args) > 0 {
		str := args[0]
		switch str {
		case "-set":
			args = args[1:]
			if len(args) < 1 {
				fmt.Fprintf(os.Stderr, "\nERROR: No argument after -set\n")
				os.Exit(1)
			}
			set := args[0]
			if set != "" && set != "-" {
				head = "<" + set + ">"
				tail = "</" + set + ">"
			}
			args = args[1:]
		case "-rec":
			args = args[1:]
			if len(args) < 1 {
				fmt.Fprintf(os.Stderr, "\nERROR: No argument after -rec\n")
				os.Exit(1)
			}
			rec := args[0]
			if rec != "" && rec != "-" {
				hd = "<" + rec + ">"
				tl = "</" + rec + ">"
			}
			args = args[1:]
		case "-skip":
			args = args[1:]
			if len(args) < 1 {
				fmt.Fprintf(os.Stderr, "\nERROR: No argument after -skip\n")
				os.Exit(1)
			}
			tmp := args[0]
			val, err := strconv.Atoi(tmp)
			if err != nil {
				fmt.Fprintf(os.Stderr, "\nERROR: -skip argument (%s) is not an integer\n", tmp)
				os.Exit(1)
			}
			skip = val
			args = args[1:]
		case "-lower":
			lower = true
			args = args[1:]
		case "-upper":
			upper = true
			args = args[1:]
		case "-indent":
			indent = true
			args = args[1:]
		case "-flush":
			indent = false
			args = args[1:]
		default:
			// remaining arguments are names for columns
			if str != "" && str != "*" {
				fields = append(fields, str)
				numFlds++
			}
			args = args[1:]
		}
	}

	if numFlds < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient arguments for %s\n", cmmd)
		os.Exit(1)
	}

	var buffer strings.Builder
	count := 0
	okay := false
	row := 0
	recordCount := 0

	wrtr := bufio.NewWriter(os.Stdout)

	scanr := bufio.NewScanner(inp)

	if head != "" {
		buffer.WriteString(head)
		buffer.WriteString("\n")
	}

	for scanr.Scan() {

		line := scanr.Text()

		row++

		if skip > 0 {
			skip--
			continue
		}

		cols := strings.Split(line, delim)

		if len(cols) != numFlds {
			fmt.Fprintf(os.Stderr, "Mismatched columns in row %d - '%s'\n", row, line)
			continue
		}

		if hd != "" {
			if indent {
				buffer.WriteString("  ")
			}
			buffer.WriteString(hd)
			buffer.WriteString("\n")
		}

		for i, fld := range fields {
			val := cols[i]
			if lower {
				val = strings.ToLower(val)
			}
			if upper {
				val = strings.ToUpper(val)
			}
			if fld[0] == '*' {
				fld = fld[1:]
			} else {
				val = html.EscapeString(val)
			}
			val = strings.TrimSpace(val)
			if indent {
				buffer.WriteString("    ")
			}
			buffer.WriteString("<")
			buffer.WriteString(fld)
			buffer.WriteString(">")
			buffer.WriteString(val)
			buffer.WriteString("</")
			buffer.WriteString(fld)
			buffer.WriteString(">")
			buffer.WriteString("\n")
		}

		if tl != "" {
			if indent {
				buffer.WriteString("  ")
			}
			buffer.WriteString(tl)
			buffer.WriteString("\n")
		}

		recordCount++
		count++

		if count >= 1000 {
			count = 0
			txt := buffer.String()
			if txt != "" {
				// print current buffer
				wrtr.WriteString(txt[:])
			}
			buffer.Reset()
		}

		okay = true
	}

	if tail != "" {
		buffer.WriteString(tail)
		buffer.WriteString("\n")
	}

	if okay {
		txt := buffer.String()
		if txt != "" {
			// print current buffer
			wrtr.WriteString(txt[:])
		}
	}
	buffer.Reset()

	wrtr.Flush()

	return recordCount
}

// READ GENBANK FLATFILE AND TRANSLATE TO INSDSEQ XML

// GenBankConverter sends INSDSeq XML records down a channel
func GenBankConverter(inp io.Reader) <-chan string {

	if inp == nil {
		return nil
	}

	out := make(chan string, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "Unable to create GenBank converter channel\n")
		os.Exit(1)
	}

	const twelvespaces = "            "
	const twentyonespaces = "                     "

	var rec strings.Builder
	var con strings.Builder
	var seq strings.Builder

	scanr := bufio.NewScanner(inp)

	convertGenBank := func(inp io.Reader, out chan<- string) {

		// close channel when all records have been sent
		defer close(out)

		row := 0

		nextLine := func() string {

			for scanr.Scan() {
				line := scanr.Text()
				if line == "" {
					continue
				}
				return line
			}
			return ""

		}

		for {

			rec.Reset()

			// read first line of next record
			line := nextLine()
			if line == "" {
				break
			}

			row++

			for {
				if !strings.HasPrefix(line, "LOCUS") {
					// skip release file header information
					line = nextLine()
					row++
					continue
				}
				break
			}

			readContinuationLines := func(str string) string {

				for {
					// read next line
					line = nextLine()
					row++
					if !strings.HasPrefix(line, twelvespaces) {
						// if not continuation line, break out of loop
						break
					}
					// append subsequent line and continue with loop
					txt := strings.TrimPrefix(line, twelvespaces)
					str += " " + txt
				}

				str = CompressRunsOfSpaces(str)
				str = strings.TrimSpace(str)

				return str
			}

			writeOneElement := func(spaces, tag, value string) {

				rec.WriteString(spaces)
				rec.WriteString("<")
				rec.WriteString(tag)
				rec.WriteString(">")
				value = html.EscapeString(value)
				rec.WriteString(value)
				rec.WriteString("</")
				rec.WriteString(tag)
				rec.WriteString(">\n")
			}

			// each section will exit with the next line ready to process

			if strings.HasPrefix(line, "LOCUS") {

				// start of record
				rec.WriteString("  <INSDSeq>\n")

				cols := strings.Fields(line)
				ln := len(cols)
				if ln == 8 {
					moleculetype := cols[4]
					strandedness := ""
					if strings.HasPrefix(moleculetype, "ds-") {
						moleculetype = strings.TrimPrefix(moleculetype, "ds-")
						strandedness = "double"
					} else if strings.HasPrefix(moleculetype, "ss-") {
						moleculetype = strings.TrimPrefix(moleculetype, "ss-")
						strandedness = "single"
					} else if strings.HasPrefix(moleculetype, "ms-") {
						moleculetype = strings.TrimPrefix(moleculetype, "ms-")
						strandedness = "mixed"
					} else if strings.HasSuffix(moleculetype, "DNA") {
						strandedness = "double"
					} else if strings.HasSuffix(moleculetype, "RNA") {
						strandedness = "single"
					}

					writeOneElement("    ", "INSDSeq_locus", cols[1])

					writeOneElement("    ", "INSDSeq_length", cols[2])

					if strandedness != "" {
						writeOneElement("    ", "INSDSeq_strandedness", strandedness)
					}

					writeOneElement("    ", "INSDSeq_moltype", moleculetype)

					writeOneElement("    ", "INSDSeq_topology", cols[5])

					writeOneElement("    ", "INSDSeq_division", cols[6])

					writeOneElement("    ", "INSDSeq_update-date", cols[7])

				} else if ln == 7 {

					writeOneElement("    ", "INSDSeq_locus", cols[1])

					writeOneElement("    ", "INSDSeq_length", cols[2])

					writeOneElement("    ", "INSDSeq_moltype", "AA")

					writeOneElement("    ", "INSDSeq_topology", cols[4])

					writeOneElement("    ", "INSDSeq_division", cols[5])

					writeOneElement("    ", "INSDSeq_update-date", cols[6])

				} else {
					fmt.Fprintf(os.Stderr, "ERROR: "+line+"\n")
				}

				// read next line and continue
				line = nextLine()
				row++
			}

			if strings.HasPrefix(line, "DEFINITION") {

				txt := strings.TrimPrefix(line, "DEFINITION")
				def := readContinuationLines(txt)
				def = strings.TrimSuffix(def, ".")

				writeOneElement("    ", "INSDSeq_definition", def)
			}

			var secondaries []string

			if strings.HasPrefix(line, "ACCESSION") {

				txt := strings.TrimPrefix(line, "ACCESSION")
				str := readContinuationLines(txt)
				accessions := strings.Fields(str)
				ln := len(accessions)
				if ln > 1 {

					writeOneElement("    ", "INSDSeq_primary-accession", accessions[0])

					// skip past primary accession, collect secondaries
					secondaries = accessions[1:]

				} else if ln == 1 {

					writeOneElement("    ", "INSDSeq_primary-accession", accessions[0])

				} else {
					fmt.Fprintf(os.Stderr, "ERROR: "+line+"\n")
				}
			}

			accnver := ""
			gi := ""

			if strings.HasPrefix(line, "VERSION") {

				cols := strings.Fields(line)
				if len(cols) == 2 {

					accnver = cols[1]
					writeOneElement("    ", "INSDSeq_accession-version", accnver)

				} else if len(cols) == 3 {

					accnver = cols[1]
					writeOneElement("    ", "INSDSeq_accession-version", accnver)

					// collect gi for other-seqids
					if strings.HasPrefix(cols[2], "GI:") {
						gi = strings.TrimPrefix(cols[2], "GI:")
					}

				} else {
					fmt.Fprintf(os.Stderr, "ERROR: "+line+"\n")
				}

				// read next line and continue
				line = nextLine()
				row++

			}

			if gi != "" {

				rec.WriteString("    <INSDSeq_other-seqids>\n")

				writeOneElement("      ", "INSDSeqid", "gi|"+gi)

				rec.WriteString("    </INSDSeq_other-seqids>\n")
			}

			if len(secondaries) > 0 {

				rec.WriteString("    <INSDSeq_secondary-accessions>\n")

				for _, secndry := range secondaries {

					writeOneElement("      ", "INSDSecondary-accn", secndry)
				}

				rec.WriteString("    </INSDSeq_secondary-accessions>\n")
			}

			if strings.HasPrefix(line, "DBLINK") {

				txt := strings.TrimPrefix(line, "DBLINK")
				readContinuationLines(txt)
				// collect for database-reference
				// out <- Token{DBLINK, dbl}
			}

			if strings.HasPrefix(line, "DBSOURCE") {

				txt := strings.TrimPrefix(line, "DBSOURCE")
				readContinuationLines(txt)
				// collect for database-source
				// out <- Token{DBSOURCE, dbl}
			}

			if strings.HasPrefix(line, "KEYWORDS") {

				txt := strings.TrimPrefix(line, "KEYWORDS")
				key := readContinuationLines(txt)
				key = strings.TrimSuffix(key, ".")

				if key != "" {
					rec.WriteString("    <INSDSeq_keywords>\n")
					kywds := strings.Split(key, ";")
					for _, kw := range kywds {
						kw = strings.TrimSpace(kw)
						if kw == "" || kw == "." {
							continue
						}

						writeOneElement("      ", "INSDKeyword", kw)
					}
					rec.WriteString("    </INSDSeq_keywords>\n")
				}
			}

			if strings.HasPrefix(line, "SOURCE") {

				txt := strings.TrimPrefix(line, "SOURCE")
				src := readContinuationLines(txt)

				writeOneElement("    ", "INSDSeq_source", src)
			}

			if strings.HasPrefix(line, "  ORGANISM") {

				org := strings.TrimPrefix(line, "  ORGANISM")
				org = CompressRunsOfSpaces(org)
				org = strings.TrimSpace(org)

				writeOneElement("    ", "INSDSeq_organism", org)

				line = nextLine()
				row++
				if strings.HasPrefix(line, twelvespaces) {
					txt := strings.TrimPrefix(line, twelvespaces)
					tax := readContinuationLines(txt)
					tax = strings.TrimSuffix(tax, ".")

					writeOneElement("    ", "INSDSeq_taxonomy", tax)
				}
			}

			rec.WriteString("    <INSDSeq_references>\n")
			for {
				if !strings.HasPrefix(line, "REFERENCE") {
					// exit out of reference section
					break
				}

				ref := "0"

				rec.WriteString("      <INSDReference>\n")

				str := strings.TrimPrefix(line, "REFERENCE")
				str = CompressRunsOfSpaces(str)
				str = strings.TrimSpace(str)
				idx := strings.Index(str, "(")
				if idx > 0 {
					ref = strings.TrimSpace(str[:idx])

					writeOneElement("        ", "INSDReference_reference", ref)

					posn := str[idx+1:]
					posn = strings.TrimSuffix(posn, ")")
					posn = strings.TrimSpace(posn)
					if posn == "sites" {

						writeOneElement("        ", "INSDReference_position", posn)

					} else {
						cols := strings.Fields(posn)
						if len(cols) == 4 && cols[2] == "to" {

							writeOneElement("        ", "INSDReference_position", cols[1]+".."+cols[3])

						} else {
							fmt.Fprintf(os.Stderr, "ERROR: "+line+"\n")
						}
					}
				} else {
					ref = strings.TrimSpace(str)

					writeOneElement("        ", "INSDReference_reference", ref)
				}
				line = nextLine()
				row++

				if strings.HasPrefix(line, "  AUTHORS") {

					txt := strings.TrimPrefix(line, "  AUTHORS")
					auths := readContinuationLines(txt)

					rec.WriteString("        <INSDReference_authors>\n")
					authors := strings.Split(auths, ", ")
					for _, auth := range authors {
						auth = strings.TrimSpace(auth)
						if auth == "" {
							continue
						}
						pair := strings.Split(auth, " and ")
						for _, name := range pair {

							writeOneElement("          ", "INSDAuthor", name)
						}
					}
					rec.WriteString("        </INSDReference_authors>\n")
				}

				if strings.HasPrefix(line, "  CONSRTM") {

					txt := strings.TrimPrefix(line, "  CONSRTM")
					cons := readContinuationLines(txt)

					writeOneElement("        ", "INSDReference_consortium", cons)
				}

				if strings.HasPrefix(line, "  TITLE") {

					txt := strings.TrimPrefix(line, "  TITLE")
					titl := readContinuationLines(txt)

					writeOneElement("        ", "INSDReference_title", titl)
				}

				if strings.HasPrefix(line, "  JOURNAL") {

					txt := strings.TrimPrefix(line, "  JOURNAL")
					jour := readContinuationLines(txt)

					writeOneElement("        ", "INSDReference_journal", jour)
				}

				if strings.HasPrefix(line, "   PUBMED") {

					txt := strings.TrimPrefix(line, "   PUBMED")
					pmid := readContinuationLines(txt)

					writeOneElement("        ", "INSDReference_pubmed", pmid)
				}

				if strings.HasPrefix(line, "  MEDLINE") {

					txt := strings.TrimPrefix(line, "  MEDLINE")
					// old MEDLINE uid not supported
					readContinuationLines(txt)
				}

				if strings.HasPrefix(line, "  REMARK") {

					txt := strings.TrimPrefix(line, "  REMARK")
					rem := readContinuationLines(txt)

					writeOneElement("        ", "INSDReference_remark", rem)
				}

				// end of this reference
				rec.WriteString("      </INSDReference>\n")
				// continue to next reference
			}
			rec.WriteString("    </INSDSeq_references>\n")

			if strings.HasPrefix(line, "COMMENT") {

				txt := strings.TrimPrefix(line, "COMMENT")
				com := readContinuationLines(txt)

				writeOneElement("    ", "INSDSeq_comment", com)
			}

			rec.WriteString("    <INSDSeq_feature-table>\n")
			if strings.HasPrefix(line, "FEATURES") {

				line = nextLine()
				row++

				for {
					if !strings.HasPrefix(line, "     ") {
						// exit out of features section
						break
					}
					if len(line) < 22 {
						fmt.Fprintf(os.Stderr, "ERROR: "+line+"\n")
						line = nextLine()
						row++
						continue
					}

					rec.WriteString("      <INSDFeature>\n")

					// read feature key and start of location
					fkey := line[5:21]
					fkey = strings.TrimSpace(fkey)

					writeOneElement("        ", "INSDFeature_key", fkey)

					loc := line[21:]
					loc = strings.TrimSpace(loc)
					for {
						line = nextLine()
						row++
						if !strings.HasPrefix(line, twentyonespaces) {
							break
						}
						txt := strings.TrimPrefix(line, twentyonespaces)
						if strings.HasPrefix(txt, "/") {
							// if not continuation of location, break out of loop
							break
						}
						// append subsequent line and continue with loop
						loc += strings.TrimSpace(txt)
					}

					writeOneElement("        ", "INSDFeature_location", loc)

					location_operator := ""
					is_comp := false
					prime5 := false
					prime3 := false

					// parseloc recursive definition
					var parseloc func(string) []string

					parseloc = func(str string) []string {

						var acc []string

						if strings.HasPrefix(str, "join(") && strings.HasSuffix(str, ")") {

							location_operator = "join"

							str = strings.TrimPrefix(str, "join(")
							str = strings.TrimSuffix(str, ")")
							items := strings.Split(str, ",")

							for _, thisloc := range items {
								inner := parseloc(thisloc)
								for _, sub := range inner {
									acc = append(acc, sub)
								}
							}

						} else if strings.HasPrefix(str, "order(") && strings.HasSuffix(str, ")") {

							location_operator = "order"

							str = strings.TrimPrefix(str, "order(")
							str = strings.TrimSuffix(str, ")")
							items := strings.Split(str, ",")

							for _, thisloc := range items {
								inner := parseloc(thisloc)
								for _, sub := range inner {
									acc = append(acc, sub)
								}
							}

						} else if strings.HasPrefix(str, "complement(") && strings.HasSuffix(str, ")") {

							is_comp = true

							str = strings.TrimPrefix(str, "complement(")
							str = strings.TrimSuffix(str, ")")
							items := parseloc(str)

							// reverse items
							for i, j := 0, len(items)-1; i < j; i, j = i+1, j-1 {
								items[i], items[j] = items[j], items[i]
							}

							// reverse from and to positions, flip direction of angle brackets (partial flags)
							for _, thisloc := range items {
								pts := strings.Split(thisloc, "..")
								ln := len(pts)
								if ln == 2 {
									fst := pts[0]
									scd := pts[1]
									lf := ""
									rt := ""
									if strings.HasPrefix(fst, "<") {
										fst = strings.TrimPrefix(fst, "<")
										rt = ">"
									}
									if strings.HasPrefix(scd, ">") {
										scd = strings.TrimPrefix(scd, ">")
										lf = "<"
									}
									acc = append(acc, lf+scd+".."+rt+fst)
								} else if ln > 0 {
									acc = append(acc, pts[0])
								}
							}

						} else {

							// save individual interval or point if no leading accession
							if strings.Index(str, ":") < 0 {
								acc = append(acc, str)
							}
						}

						return acc
					}

					items := parseloc(loc)

					rec.WriteString("        <INSDFeature_intervals>\n")

					num_ivals := 0

					// report individual intervals
					for _, thisloc := range items {
						if thisloc == "" {
							continue
						}

						num_ivals++

						rec.WriteString("          <INSDInterval>\n")
						pts := strings.Split(thisloc, "..")
						if len(pts) == 2 {

							// fr..to
							fr := pts[0]
							to := pts[1]
							if strings.HasPrefix(fr, "<") {
								fr = strings.TrimPrefix(fr, "<")
								prime5 = true
							}
							if strings.HasPrefix(to, ">") {
								to = strings.TrimPrefix(to, ">")
								prime3 = true
							}
							writeOneElement("            ", "INSDInterval_from", fr)
							writeOneElement("            ", "INSDInterval_to", to)
							if is_comp {
								rec.WriteString("            <INSDInterval_iscomp value=\"true\"/>\n")
							}
							writeOneElement("            ", "INSDInterval_accession", accnver)

						} else {

							crt := strings.Split(thisloc, "^")
							if len(crt) == 2 {

								// fr^to
								fr := crt[0]
								to := crt[1]
								writeOneElement("            ", "INSDInterval_from", fr)
								writeOneElement("            ", "INSDInterval_to", to)
								if is_comp {
									rec.WriteString("            <INSDInterval_iscomp value=\"true\"/>\n")
								}
								rec.WriteString("            <INSDInterval_interbp value=\"true\"/>\n")
								writeOneElement("            ", "INSDInterval_accession", accnver)

							} else {

								// pt
								pt := pts[0]
								if strings.HasPrefix(pt, "<") {
									pt = strings.TrimPrefix(pt, "<")
									prime5 = true
								}
								if strings.HasPrefix(pt, ">") {
									pt = strings.TrimPrefix(pt, ">")
									prime3 = true
								}
								writeOneElement("            ", "INSDInterval_point", pt)
								writeOneElement("            ", "INSDInterval_accession", accnver)
							}
						}
						rec.WriteString("          </INSDInterval>\n")
					}

					rec.WriteString("        </INSDFeature_intervals>\n")

					if num_ivals > 1 {
						writeOneElement("        ", "INSDFeature_operator", location_operator)
					}
					if prime5 {
						rec.WriteString("        <INSDFeature_partial5 value=\"true\"/>\n")
					}
					if prime3 {
						rec.WriteString("        <INSDFeature_partial3 value=\"true\"/>\n")
					}

					hasQual := false
					for {
						if !strings.HasPrefix(line, twentyonespaces) {
							// if not qualifier line, break out of loop
							break
						}
						txt := strings.TrimPrefix(line, twentyonespaces)
						qual := ""
						val := ""
						if strings.HasPrefix(txt, "/") {
							if !hasQual {
								hasQual = true
								rec.WriteString("        <INSDFeature_quals>\n")
							}
							// read new qualifier and start of value
							qual = strings.TrimPrefix(txt, "/")
							qual = strings.TrimSpace(qual)
							idx := strings.Index(qual, "=")
							if idx > 0 {
								val = qual[idx+1:]
								qual = qual[:idx]
							}

							for {
								line = nextLine()
								row++
								if !strings.HasPrefix(line, twentyonespaces) {
									break
								}
								txt := strings.TrimPrefix(line, twentyonespaces)
								if strings.HasPrefix(txt, "/") {
									// if not continuation of qualifier, break out of loop
									break
								}
								// append subsequent line to value and continue with loop
								if qual == "transcription" || qual == "translation" || qual == "peptide" || qual == "anticodon" {
									val += strings.TrimSpace(txt)
								} else {
									val += " " + strings.TrimSpace(txt)
								}
							}

							rec.WriteString("          <INSDQualifier>\n")

							writeOneElement("            ", "INSDQualifier_name", qual)

							val = strings.TrimPrefix(val, "\"")
							val = strings.TrimSuffix(val, "\"")
							val = strings.TrimSpace(val)
							if val != "" {

								writeOneElement("            ", "INSDQualifier_value", val)
							}

							rec.WriteString("          </INSDQualifier>\n")
						}
					}
					if hasQual {
						rec.WriteString("        </INSDFeature_quals>\n")
					}

					// end of this feature
					rec.WriteString("      </INSDFeature>\n")
					// continue to next feature
				}
			}
			rec.WriteString("    </INSDSeq_feature-table>\n")

			if strings.HasPrefix(line, "CONTIG") {

				// pathological records can have over 90,000 components, use strings.Builder
				con.Reset()

				txt := strings.TrimPrefix(line, "CONTIG")
				txt = strings.TrimSpace(txt)
				con.WriteString(txt)
				for {
					// read next line
					line = nextLine()
					row++
					if !strings.HasPrefix(line, twelvespaces) {
						// if not continuation of contig, break out of loop
						break
					}
					// append subsequent line and continue with loop
					txt = strings.TrimPrefix(line, twelvespaces)
					txt = strings.TrimSpace(txt)
					con.WriteString(txt)
				}
			}

			if strings.HasPrefix(line, "BASE COUNT") {

				txt := strings.TrimPrefix(line, "BASE COUNT")
				readContinuationLines(txt)
				// not supported
			}

			if strings.HasPrefix(line, "ORIGIN") {

				line = nextLine()
				row++
			}

			// remainder should be sequence

			// sequence can be millions of bases, use strings.Builder
			seq.Reset()

			for line != "" {

				if strings.HasPrefix(line, "//") {

					// end of record, print collected sequence
					str := seq.String()
					if str != "" {

						writeOneElement("    ", "INSDSeq_sequence", str)
					}
					seq.Reset()

					// print contig section
					str = con.String()
					str = strings.TrimSpace(str)
					if str != "" {
						writeOneElement("    ", "INSDSeq_contig", str)
					}
					con.Reset()

					// end of record
					rec.WriteString("  </INSDSeq>\n")

					// send formatted record down channel
					txt := rec.String()
					out <- txt
					rec.Reset()
					// go to top of loop for next record
					break
				}

				// read next sequence line

				cols := strings.Fields(line)
				for _, str := range cols {

					if IsAllDigits(str) {
						continue
					}

					// append letters to sequence
					seq.WriteString(str)
				}

				// read next line and continue
				line = nextLine()
				row++

			}

			// continue to next record
		}
	}

	// launch single converter goroutine
	go convertGenBank(inp, out)

	return out
}

// MAIN FUNCTION

// e.g., xtract -pattern PubmedArticle -element MedlineCitation/PMID -block Author -sep " " -element Initials,LastName

func main() {

	// skip past executable name
	args := os.Args[1:]

	if len(args) < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: No command-line arguments supplied to xtract\n")
		os.Exit(1)
	}

	// CONCURRENCY, CLEANUP, AND DEBUGGING FLAGS

	// do these first because -defcpu and -maxcpu can be sent from wrapper before other arguments

	ncpu := runtime.NumCPU()
	if ncpu < 1 {
		ncpu = 1
	}

	// wrapper can limit maximum number of processors to use (undocumented)
	maxProcs := ncpu
	defProcs := 0

	// concurrent performance tuning parameters, can be overridden by -proc and -cons
	numProcs := 0
	serverRatio := 4

	// number of servers usually calculated by -cons server ratio, but can be overridden by -serv
	NumServe = 0

	// number of channels usually equals number of servers, but can be overridden by -chan
	ChanDepth = 0

	// miscellaneous tuning parameters
	HeapSize = 16
	FarmSize = 64

	// garbage collector control can be set by environment variable or default value with -gogc 0
	goGc := 600

	// -flag sets -strict or -mixed cleanup flags from argument
	flgs := ""

	DeStop = true

	unicodePolicy := ""
	scriptPolicy := ""
	mathmlPolicy := ""

	// read data from file instead of stdin
	fileName := ""

	// debugging
	dbug := false
	mpty := false
	idnt := false
	stts := false
	timr := false

	// profiling
	prfl := false

	// repeat the specified extraction 5 times for each -proc from 1 to nCPU
	trial := false

	// get numeric value
	getNumericArg := func(name string, zer, min, max int) int {

		if len(args) < 2 {
			fmt.Fprintf(os.Stderr, "\nERROR: %s is missing\n", name)
			os.Exit(1)
		}
		value, err := strconv.Atoi(args[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "\nERROR: %s (%s) is not an integer\n", name, args[1])
			os.Exit(1)
		}
		// skip past first of two arguments
		args = args[1:]

		// special case for argument value of 0
		if value < 1 {
			return zer
		}
		// limit value to between specified minimum and maximum
		if value < min {
			return min
		}
		if value > max {
			return max
		}
		return value
	}

	inSwitch := true

	// get concurrency, cleanup, and debugging flags in any order
	for {

		inSwitch = true

		switch args[0] {
		// concurrency override arguments can be passed in by local wrapper script (undocumented)
		case "-maxcpu":
			maxProcs = getNumericArg("Maximum number of processors", 1, 1, ncpu)
		case "-defcpu":
			defProcs = getNumericArg("Default number of processors", ncpu, 1, ncpu)
		// performance tuning flags
		case "-proc":
			numProcs = getNumericArg("Number of processors", ncpu, 1, ncpu)
		case "-cons":
			serverRatio = getNumericArg("Parser to processor ratio", 4, 1, 32)
		case "-serv":
			NumServe = getNumericArg("Concurrent parser count", 0, 1, 128)
		case "-chan":
			ChanDepth = getNumericArg("Communication channel depth", 0, ncpu, 128)
		case "-heap":
			HeapSize = getNumericArg("Unshuffler heap size", 8, 8, 64)
		case "-farm":
			FarmSize = getNumericArg("Node buffer length", 4, 4, 2048)
		case "-gogc":
			goGc = getNumericArg("Garbage collection percentage", 0, 50, 1000)

		// read data from file
		case "-input":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Input file name is missing\n")
				os.Exit(1)
			}
			fileName = args[1]
			// skip past first of two arguments
			args = args[1:]

		// data cleanup flags
		case "-compress", "-compressed":
			DoCompress = true
		case "-spaces", "-cleanup":
			DoCleanup = true
		case "-strict":
			DoStrict = true
			AllowEmbed = true
			ContentMods = true
		case "-mixed":
			DoMixed = true
			AllowEmbed = true
			ContentMods = true
		case "-accent":
			DeAccent = true
		case "-ascii":
			DoASCII = true

		// previously visible processing flags (undocumented)
		case "-stems", "-stem":
			DoStem = true
		case "-stops", "-stop":
			DeStop = false

		// allow setting of unicode, script, and mathml flags (undocumented)
		case "-unicode":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Unicode argument is missing\n")
				os.Exit(1)
			}
			unicodePolicy = args[1]
			// skip past first of two arguments
			args = args[1:]
		case "-script":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Script argument is missing\n")
				os.Exit(1)
			}
			scriptPolicy = args[1]
			// skip past first of two arguments
			args = args[1:]
		case "-mathml":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: MathML argument is missing\n")
				os.Exit(1)
			}
			mathmlPolicy = args[1]
			// skip past first of two arguments
			args = args[1:]

		case "-flag", "-flags":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Flags argument is missing\n")
				os.Exit(1)
			}
			flgs = args[1]
			// skip past first of two arguments
			args = args[1:]

		// debugging flags
		case "-debug":
			dbug = true
		case "-empty":
			mpty = true
		case "-ident":
			idnt = true
		case "-stats", "-stat":
			stts = true
		case "-timer":
			timr = true
		case "-profile":
			prfl = true
		case "-trial", "-trials":
			trial = true

		default:
			// if not any of the controls, set flag to break out of for loop
			inSwitch = false
		}

		if !inSwitch {
			break
		}

		// skip past argument
		args = args[1:]

		if len(args) < 1 {
			break
		}
	}

	// -flag allows script to set -strict or -mixed (or -stems, or -stops) from argument
	switch flgs {
	case "strict":
		DoStrict = true
	case "mixed":
		DoMixed = true
	case "stems", "stem":
		DoStem = true
	case "stops", "stop":
		DeStop = false
	case "none", "default":
	default:
		if flgs != "" {
			fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized -flag value '%s'\n", flgs)
			os.Exit(1)
		}
	}

	UnicodeFix = ParseMarkup(unicodePolicy, "-unicode")
	ScriptFix = ParseMarkup(scriptPolicy, "-script")
	MathMLFix = ParseMarkup(mathmlPolicy, "-mathml")

	if UnicodeFix != NOMARKUP {
		DoUnicode = true
	}

	if ScriptFix != NOMARKUP {
		DoScript = true
	}

	if MathMLFix != NOMARKUP {
		DoMathML = true
	}

	// set dependent flags
	CountLines = DoMixed
	AllowEmbed = DoStrict || DoMixed
	ContentMods = AllowEmbed || DoCompress || DoUnicode || DoScript || DoMathML || DeAccent || DoASCII

	// reality checks on number of processors to use
	// performance degrades if capacity is above maximum number of partitions per second (context switching?)
	if numProcs == 0 {
		if defProcs > 0 {
			numProcs = defProcs
		} else {
			// best performance measurement with current code is obtained when 6 to 8 processors are assigned,
			// varying slightly among queries on PubmedArticle, gene DocumentSummary, and INSDSeq sequence records
			numProcs = 8
			if cpuid.CPU.ThreadsPerCore > 1 {
				cores := ncpu / cpuid.CPU.ThreadsPerCore
				if cores > 4 && cores < 8 {
					numProcs = cores
				}
			}
		}
	}
	if numProcs > ncpu {
		numProcs = ncpu
	}
	if numProcs > maxProcs {
		numProcs = maxProcs
	}

	// allow simultaneous threads for multiplexed goroutines
	runtime.GOMAXPROCS(numProcs)

	// adjust garbage collection target percentage
	if goGc >= 50 && goGc <= 1000 {
		debug.SetGCPercent(goGc)
	}

	// explicit -serv argument overrides -cons ratio
	if NumServe > 0 {
		serverRatio = NumServe / numProcs
		// if numServers / numProcs is not a whole number, do not print serverRatio in -stats
		if NumServe != numProcs*serverRatio {
			serverRatio = 0
		}
	} else {
		NumServe = numProcs * serverRatio
	}
	// server limits
	if NumServe > 128 {
		NumServe = 128
	} else if NumServe < 1 {
		NumServe = numProcs
	}

	// explicit -chan argument overrides default to number of servers
	if ChanDepth == 0 {
		ChanDepth = NumServe
	}

	// -stats prints number of CPUs and performance tuning values if no other arguments (undocumented)
	if stts && len(args) < 1 {

		fmt.Fprintf(os.Stderr, "Core %d\n", ncpu/cpuid.CPU.ThreadsPerCore)
		fmt.Fprintf(os.Stderr, "Thrd %d\n", ncpu)
		fmt.Fprintf(os.Stderr, "Sock %d\n", ncpu/cpuid.CPU.LogicalCores)
		fmt.Fprintf(os.Stderr, "Mmry %d\n", memory.TotalMemory()/(1024*1024*1024))

		fmt.Fprintf(os.Stderr, "Proc %d\n", numProcs)
		if serverRatio > 0 {
			fmt.Fprintf(os.Stderr, "Cons %d\n", serverRatio)
		}
		fmt.Fprintf(os.Stderr, "Serv %d\n", NumServe)
		fmt.Fprintf(os.Stderr, "Chan %d\n", ChanDepth)
		fmt.Fprintf(os.Stderr, "Heap %d\n", HeapSize)
		fmt.Fprintf(os.Stderr, "Farm %d\n", FarmSize)
		fmt.Fprintf(os.Stderr, "Gogc %d\n", goGc)

		fi, err := os.Stdin.Stat()
		if err == nil {
			mode := fi.Mode().String()
			fmt.Fprintf(os.Stderr, "Mode %s\n", mode)
		}

		fmt.Fprintf(os.Stderr, "\n")

		return
	}

	if len(args) < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to xtract\n")
		os.Exit(1)
	}

	// DOCUMENTATION COMMANDS

	inSwitch = true

	switch args[0] {
	case "-version":
		fmt.Printf("%s\n", xtractVersion)
	case "-help":
		fmt.Printf("xtract %s\n%s\n", xtractVersion, xtractHelp)
	case "-examples", "-example":
		ex, eerr := os.Executable()
		if eerr == nil {
			fmt.Printf("xtract %s\n\n", xtractVersion)
			exPath := filepath.Dir(ex)
			fpath := path.Join(exPath, "hlp-xtract.txt")
			file, ferr := os.Open(fpath)
			if file != nil && ferr == nil {
				scanner := bufio.NewScanner(file)
				for scanner.Scan() {
					fmt.Println(scanner.Text())
				}
			}
			file.Close()
			fmt.Printf("\n")
		}
	case "-extras", "-extra", "-advanced":
		fmt.Printf("Please run rchive -help for local record indexing information\n")
	case "-internal", "-internals":
		fmt.Printf("xtract %s\n%s\n", xtractVersion, xtractInternal)
	case "-keys":
		fmt.Printf("%s\n", keyboardShortcuts)
	case "-unix":
		fmt.Printf("%s\n", unixCommands)
	default:
		// if not any of the documentation commands, keep going
		inSwitch = false
	}

	if inSwitch {
		return
	}

	// FILE NAME CAN BE SUPPLIED WITH -input COMMAND

	in := os.Stdin

	// check for data being piped into stdin
	isPipe := false
	fi, err := os.Stdin.Stat()
	if err == nil {
		isPipe = bool((fi.Mode() & os.ModeNamedPipe) != 0)
	}

	usingFile := false

	if fileName != "" {

		inFile, err := os.Open(fileName)
		if err != nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to open input file '%s'\n", fileName)
			os.Exit(1)
		}

		defer inFile.Close()

		// use indicated file instead of stdin
		in = inFile
		usingFile = true

		if isPipe && runtime.GOOS != "windows" {
			mode := fi.Mode().String()
			fmt.Fprintf(os.Stderr, "\nERROR: Input data from both stdin and file '%s', mode is '%s'\n", fileName, mode)
			os.Exit(1)
		}
	}

	// check for -input command after extraction arguments
	for _, str := range args {
		if str == "-input" {
			fmt.Fprintf(os.Stderr, "\nERROR: Misplaced -input command\n")
			os.Exit(1)
		}
	}

	// START PROFILING IF REQUESTED

	if prfl {

		f, err := os.Create("cpu.pprof")
		if err != nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to create profile output file\n")
			os.Exit(1)
		}

		pprof.StartCPUProfile(f)

		defer pprof.StopCPUProfile()
	}

	// INITIALIZE RECORD COUNT

	recordCount := 0
	byteCount := 0

	// print processing rate and program duration
	printDuration := func(name string) {

		PrintDuration(name, recordCount, byteCount)
	}

	// JSON TO XML CONVERTER

	if args[0] == "-j2x" || args[0] == "-json2xml" {

		set := "root"
		rec := ""
		nest := ""

		nextArg := func() (string, bool) {

			if len(args) < 1 {
				return "", false
			}

			// remove next token from slice
			nxt := args[0]
			args = args[1:]

			return nxt, true
		}

		// look for optional arguments
		args = args[1:]
		for {
			arg, ok := nextArg()
			if !ok {
				break
			}

			switch arg {
			case "-set":
				// override set wrapper
				set, ok = nextArg()
				if ok && set == "-" {
					set = ""
				}
			case "-rec":
				// override record wrapper
				rec, ok = nextArg()
				if ok && rec == "-" {
					rec = ""
				}
			case "-nest":
				// specify nested array naming policy
				nest, ok = nextArg()
				if !ok {
					fmt.Fprintf(os.Stderr, "Nested array naming policy is missing\n")
					os.Exit(1)
				}
				if ok && nest == "-" {
					nest = "flat"
				}
				switch nest {
				case "flat", "plural", "name", "recurse", "recursive", "same", "depth", "deep", "level":
				default:
					fmt.Fprintf(os.Stderr, "Unrecognized nested array naming policy\n")
					os.Exit(1)
				}
			default:
				// alternative form uses positional arguments to override set and rec
				set = arg
				if set == "-" {
					set = ""
				}
				rec, ok = nextArg()
				if ok && rec == "-" {
					rec = ""
				}
			}
		}

		// use output channel of tokenizer as input channel of converter
		jtkn := JSONTokenizer(in)
		jcnv := JSONConverter(jtkn, set, rec, nest)

		if jtkn == nil || jcnv == nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to create JSON to XML converter\n")
			os.Exit(1)
		}

		if set != "" {
			fmt.Fprintf(os.Stdout, "<%s>\n", set)
		}

		// drain output of last channel in service chain
		for str := range jcnv {

			if str == "" {
				continue
			}

			// send result to output
			os.Stdout.WriteString(str)
			if !strings.HasSuffix(str, "\n") {
				os.Stdout.WriteString("\n")
			}

			recordCount++
			runtime.Gosched()
		}

		if set != "" {
			fmt.Fprintf(os.Stdout, "</%s>\n", set)
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// NAME OF OUTPUT STRING TRANSFORMATION FILE

	tform := ""
	transform := make(map[string]string)

	populateTx := func(tf string) {

		inFile, err := os.Open(tf)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Unable to open transformation file %s\n", err.Error())
			os.Exit(1)
		}
		defer inFile.Close()

		scanr := bufio.NewScanner(inFile)

		// populate transformation map for -translate (and -matrix) output
		for scanr.Scan() {

			line := scanr.Text()
			frst, scnd := SplitInTwoAt(line, "\t", LEFT)

			transform[frst] = scnd
		}
	}

	if len(args) > 2 && args[0] == "-transform" {
		tform = args[1]
		args = args[2:]
		if tform != "" {
			populateTx(tform)
		}
	}

	// READ TAB-DELIMITED FILE AND WRAP IN XML FIELDS

	// must be called before CreateReader starts draining stdin
	if len(args) > 1 && args[0] == "-t2x" {

		recordCount = TableConverter(in, "\t", args)

		debug.FreeOSMemory()

		if timr {
			printDuration("lines")
		}

		return
	}

	if len(args) > 1 && args[0] == "-c2x" {

		recordCount = TableConverter(in, ",", args)

		debug.FreeOSMemory()

		if timr {
			printDuration("lines")
		}

		return
	}

	// READ GENBANK FLATFILE AND TRANSLATE TO INSDSEQ XML

	// must be called before CreateReader starts draining stdin
	if len(args) > 0 && args[0] == "-g2x" {

		gbk := GenBankConverter(in)

		if gbk == nil {
			fmt.Fprintf(os.Stderr, "Unable to create GenBank to XML converter\n")
			os.Exit(1)
		}

		head := `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE INSDSet PUBLIC "-//NCBI//INSD INSDSeq/EN" "http://www.ncbi.nlm.nih.gov/dtd/INSD_INSDSeq.dtd">
<INSDSet>
`
		tail := ""

		// drain output of last channel in service chain
		for str := range gbk {

			if str == "" {
				continue
			}

			if head != "" {
				os.Stdout.WriteString(head)
				head = ""
				tail = `</INSDSet>
`
			}

			// send result to stdout
			os.Stdout.WriteString(str)
			if !strings.HasSuffix(str, "\n") {
				os.Stdout.WriteString("\n")
			}

			recordCount++

			runtime.Gosched()
		}

		if tail != "" {
			os.Stdout.WriteString(tail)
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// CREATE XML BLOCK READER FROM STDIN OR FILE

	rdr := CreateReader(in)
	if rdr == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create XML Block Reader\n")
		os.Exit(1)
	}

	// SEQUENCE RECORD EXTRACTION COMMAND GENERATOR

	// -insd simplifies extraction of INSDSeq qualifiers
	if args[0] == "-insd" || args[0] == "-insd-" || args[0] == "-insd-idx" {

		addDash := true
		doIndex := false
		// -insd- variant suppresses use of dash as placeholder for missing qualifiers (undocumented)
		if args[0] == "-insd-" {
			addDash = false
		}
		// -insd-idx variant creates word index using -indices command (undocumented)
		if args[0] == "-insd-idx" {
			doIndex = true
			addDash = false
		}

		args = args[1:]

		insd := ProcessINSD(args, isPipe || usingFile, addDash, doIndex)

		if !isPipe && !usingFile {
			// no piped input, so write output instructions
			fmt.Printf("xtract")
			for _, str := range insd {
				fmt.Printf(" %s", str)
			}
			fmt.Printf("\n")
			return
		}

		// data in pipe, so replace arguments, execute dynamically
		args = insd
	}

	// CITATION MATCHER EXTRACTION COMMAND GENERATOR

	// -hydra filters HydraResponse output by relevance score (undocumented)
	if args[0] == "-hydra" {

		hydra := ProcessHydra(isPipe || usingFile)

		if !isPipe && !usingFile {
			// no piped input, so write output instructions
			fmt.Printf("xtract")
			for _, str := range hydra {
				fmt.Printf(" %s", str)
			}
			fmt.Printf("\n")
			return
		}

		// data in pipe, so replace arguments, execute dynamically
		args = hydra
	}

	// BIOTHINGS EXTRACTION COMMAND GENERATOR

	// -biopath takes a parent object and a dotted exploration path for BioThings resources (undocumented)
	if args[0] == "-biopath" {

		args = args[1:]

		biopath := ProcessBiopath(args, isPipe || usingFile)

		if !isPipe && !usingFile {
			// no piped input, so write output instructions
			fmt.Printf("xtract")
			for _, str := range biopath {
				fmt.Printf(" %s", str)
			}
			fmt.Printf("\n")
			return
		}

		// data in pipe, so replace arguments, execute dynamically
		args = biopath
	}

	// ENTREZ2INDEX COMMAND GENERATOR

	// -e2index shortcut for experimental indexing code (documented in rchive.go)
	if args[0] == "-e2index" {

		// e.g., xtract -transform "$EDIRECT_MESH_TREE" -e2index

		args = args[1:]

		if len(args) == 0 {
			// if no arguments, use default values
			args = []string{"PubmedArticle", "MedlineCitation/PMID", "ArticleTitle,Abstract/AbstractText"}
		}

		// environment variable can override garbage collector (undocumented)
		gcEnv := os.Getenv("EDIRECT_INDEX_GOGC")
		if gcEnv != "" {
			val, err := strconv.Atoi(gcEnv)
			if err == nil {
				if val >= 50 && val <= 1000 {
					debug.SetGCPercent(val)
				} else {
					debug.SetGCPercent(100)
				}
			}
		}

		// environment variable can override number of servers (undocumented)
		svEnv := os.Getenv("EDIRECT_INDEX_SERV")
		if svEnv != "" {
			val, err := strconv.Atoi(svEnv)
			if err == nil {
				if val >= 1 && val <= 128 {
					NumServe = val
				} else {
					NumServe = 1
				}
			}
		}

		res := ProcessE2Index(args, tform, isPipe || usingFile)

		if !isPipe && !usingFile {
			// no piped input, so write output instructions
			fmt.Printf("xtract")
			if tform != "" {
				fmt.Printf(" -transform %s", tform)
			}
			for _, str := range res {
				fmt.Printf(" %s", str)
			}
			fmt.Printf("\n")
			return
		}

		// data in pipe, so replace arguments, execute dynamically
		args = res
	}

	// CONFIRM INPUT DATA AVAILABILITY AFTER RUNNING COMMAND GENERATORS

	if fileName == "" && runtime.GOOS != "windows" {

		fromStdin := bool((fi.Mode() & os.ModeCharDevice) == 0)
		if !isPipe || !fromStdin {
			mode := fi.Mode().String()
			fmt.Fprintf(os.Stderr, "\nERROR: No data supplied to xtract from stdin or file, mode is '%s'\n", mode)
			os.Exit(1)
		}
	}

	if !usingFile && !isPipe {

		fmt.Fprintf(os.Stderr, "\nERROR: No XML input data supplied to xtract\n")
		os.Exit(1)
	}

	// SPECIAL FORMATTING COMMANDS

	inSwitch = true
	leaf := false

	switch args[0] {
	case "-format":
		recordCount = ProcessFormat(rdr, args, timr)
	case "-verify", "-validate":
		recordCount = ProcessVerify(rdr, args)
	case "-filter":
		ProcessFilter(rdr, args)
	case "-normalize", "-normal":
		ProcessNormalize(rdr, args)
	case "-outline":
		ProcessOutline(rdr)
	case "-contour":
		leaf = true
		fallthrough
	case "-synopsis":
		args = args[1:]
		delim := "/"
		if len(args) > 0 {
			delim = args[0]
			if len(delim) > 3 {
				delim = "/"
			}
		}
		ProcessSynopsis(rdr, leaf, delim)
	case "-tokens":
		ProcessTokens(rdr)
	default:
		// if not any of the formatting commands, keep going
		inSwitch = false
	}

	if inSwitch {

		debug.FreeOSMemory()

		// suppress printing of lines if not properly counted
		if recordCount == 1 {
			recordCount = 0
		}

		if timr {
			printDuration("lines")
		}

		return
	}

	// MISCELLANEOUS TIMING COMMANDS

	if args[0] == "-chunk" {

		for str := range rdr {
			recordCount++
			byteCount += len(str)
		}

		printDuration("blocks")

		return
	}

	if args[0] == "-split" {

		if len(args) > 1 {
			if args[1] == "-pattern" {
				// skip past -split if followed by -pattern
				args = args[1:]
			}
		}
		if len(args) < 2 {
			fmt.Fprintf(os.Stderr, "\nERROR: Pattern missing after -split command\n")
			os.Exit(1)
		}
		pat := args[1]

		PartitionPattern(pat, "", rdr,
			func(str string) {
				recordCount++
				byteCount += len(str)
			})

		printDuration("patterns")

		return
	}

	if args[0] == "-token" {

		ParseXML("", "", rdr,
			func(tkn Token) {
				recordCount++
				byteCount += len(tkn.Name) + len(tkn.Attr)
			},
			nil, nil)

		printDuration("tokens")

		return
	}

	// SPECIFY STRINGS TO GO BEFORE AND AFTER ENTIRE OUTPUT OR EACH RECORD

	head := ""
	tail := ""

	hd := ""
	tl := ""

	for {

		inSwitch = true

		switch args[0] {
		case "-head":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Pattern missing after -head command\n")
				os.Exit(1)
			}
			head = ConvertSlash(args[1])
		case "-tail":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Pattern missing after -tail command\n")
				os.Exit(1)
			}
			tail = ConvertSlash(args[1])
		case "-hd":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Pattern missing after -hd command\n")
				os.Exit(1)
			}
			hd = ConvertSlash(args[1])
		case "-tl":
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Pattern missing after -tl command\n")
				os.Exit(1)
			}
			tl = ConvertSlash(args[1])
		case "-wrp":
			// shortcut to wrap records in XML tags
			if len(args) < 2 {
				fmt.Fprintf(os.Stderr, "\nERROR: Pattern missing after -wrp command\n")
				os.Exit(1)
			}
			tmp := ConvertSlash(args[1])
			lft, rgt := SplitInTwoAt(tmp, ",", LEFT)
			if lft != "" {
				head = "<" + lft + ">"
				tail = "</" + lft + ">"
			}
			if rgt != "" {
				hd = "<" + rgt + ">"
				tl = "</" + rgt + ">"
			}
		default:
			// if not any of the controls, set flag to break out of for loop
			inSwitch = false
		}

		if !inSwitch {
			break
		}

		// skip past arguments
		args = args[2:]

		if len(args) < 1 {
			fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to xtract\n")
			os.Exit(1)
		}
	}

	// ENSURE PRESENCE OF PATTERN ARGUMENT

	if len(args) < 1 {
		fmt.Fprintf(os.Stderr, "\nERROR: Insufficient command-line arguments supplied to xtract\n")
		os.Exit(1)
	}

	// allow -record as synonym of -pattern (undocumented)
	if args[0] == "-record" || args[0] == "-Record" {
		args[0] = "-pattern"
	}

	// make sure top-level -pattern command is next
	if args[0] != "-pattern" && args[0] != "-Pattern" {
		fmt.Fprintf(os.Stderr, "\nERROR: No -pattern in command-line arguments\n")
		os.Exit(1)
	}
	if len(args) < 2 {
		fmt.Fprintf(os.Stderr, "\nERROR: Item missing after -pattern command\n")
		os.Exit(1)
	}

	topPat := args[1]
	if topPat == "" {
		fmt.Fprintf(os.Stderr, "\nERROR: Item missing after -pattern command\n")
		os.Exit(1)
	}
	if strings.HasPrefix(topPat, "-") {
		fmt.Fprintf(os.Stderr, "\nERROR: Misplaced %s command\n", topPat)
		os.Exit(1)
	}

	// look for -pattern Parent/* construct for heterogeneous data, e.g., -pattern PubmedArticleSet/*
	topPattern, star := SplitInTwoAt(topPat, "/", LEFT)
	if topPattern == "" {
		return
	}

	parent := ""
	if star == "*" {
		parent = topPattern
	} else if star != "" {
		fmt.Fprintf(os.Stderr, "\nERROR: -pattern Parent/Child construct is not supported\n")
		os.Exit(1)
	}

	// READ FILE OF IDENTIFIERS AND CONCURRENTLY EXTRACT SELECTED RECORDS

	// -pattern record_name -select parent/element@attribute^version -in file_of_identifiers
	if len(args) == 6 && args[2] == "-select" && (args[4] == "-in" || args[4] == "-retaining") {

		indx := args[3]
		unqe := args[5]

		// read file of identifiers to use for filtering
		fl, err := os.Open(unqe)
		if err != nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to open identifier file '%s'\n", unqe)
			os.Exit(1)
		}

		// create map that records each UID
		order := make(map[string]bool)

		scanr := bufio.NewScanner(fl)

		// read lines of identifiers
		for scanr.Scan() {

			line := scanr.Text()
			id, _ := SplitInTwoAt(line, "\t", LEFT)

			id = SortStringByWords(id)

			// add identifier to map
			order[id] = true
		}

		fl.Close()

		xmlq := CreateProducer(topPattern, star, rdr)
		fchq := CreateSelectors(topPattern, indx, order, xmlq)
		unsq := CreateUnshuffler(fchq)

		if xmlq == nil || fchq == nil || unsq == nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to create selector\n")
			os.Exit(1)
		}

		if head != "" {
			os.Stdout.WriteString(head)
			os.Stdout.WriteString("\n")
		}

		// drain output channel
		for curr := range unsq {

			str := curr.Text

			if str == "" {
				continue
			}

			if hd != "" {
				os.Stdout.WriteString(hd)
				os.Stdout.WriteString("\n")
			}

			// send result to output
			os.Stdout.WriteString(str)
			if !strings.HasSuffix(str, "\n") {
				os.Stdout.WriteString("\n")
			}

			if tl != "" {
				os.Stdout.WriteString(tl)
				os.Stdout.WriteString("\n")
			}

			recordCount++
			runtime.Gosched()
		}

		if tail != "" {
			os.Stdout.WriteString(tail)
			os.Stdout.WriteString("\n")
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// READ FILE OF IDENTIFIERS AND EXCLUDE SELECTED RECORDS

	// -pattern record_name -exclude element -excluding file_of_identifiers (undocumented)
	if len(args) == 6 && args[2] == "-select" && args[4] == "-excluding" {

		indx := args[3]
		unqe := args[5]

		// read file of identifiers to use for filtering
		fl, err := os.Open(unqe)
		if err != nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to open identifier file '%s'\n", unqe)
			os.Exit(1)
		}

		// create map that records each UID
		order := make(map[string]bool)

		scanr := bufio.NewScanner(fl)

		// read lines of identifiers
		for scanr.Scan() {

			line := scanr.Text()
			id, _ := SplitInTwoAt(line, "\t", LEFT)
			id = strings.ToLower(id)

			// add identifier to map
			order[id] = true
		}

		fl.Close()

		find := ParseIndex(indx)

		if head != "" {
			os.Stdout.WriteString(head)
			os.Stdout.WriteString("\n")
		}

		PartitionPattern(topPattern, star, rdr,
			func(str string) {
				recordCount++

				id := FindIdentifier(str[:], parent, find)
				if id != "" {
					id = strings.ToLower(id)
					_, ok := order[id]
					if ok {
						// in exclusion list, skip
						return
					}
				}

				if hd != "" {
					os.Stdout.WriteString(hd)
					os.Stdout.WriteString("\n")
				}

				// write selected record
				os.Stdout.WriteString(str[:])
				os.Stdout.WriteString("\n")

				if tl != "" {
					os.Stdout.WriteString(tl)
					os.Stdout.WriteString("\n")
				}
			})

		if tail != "" {
			os.Stdout.WriteString(tail)
			os.Stdout.WriteString("\n")
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// READ ORDERED FILE OF IDENTIFIERS AND XML STRINGS, APPEND XML JUST INSIDE CLOSING TAG OF APPROPRIATE RECORD

	// -pattern record_name -select element -appending file_of_identifiers_and_metadata (undocumented)
	if len(args) == 6 && args[2] == "-select" && args[4] == "-appending" {

		indx := args[3]
		apnd := args[5]

		fl, err := os.Open(apnd)
		if err != nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to open transformation file '%s'\n", apnd)
			os.Exit(1)
		}

		scanr := bufio.NewScanner(fl)

		find := ParseIndex(indx)

		if head != "" {
			os.Stdout.WriteString(head)
			os.Stdout.WriteString("\n")
		}

		rgt := "</" + topPattern + ">"

		PartitionPattern(topPattern, star, rdr,
			func(str string) {
				recordCount++

				id := FindIdentifier(str[:], parent, find)
				if id == "" {
					return
				}
				id = strings.ToLower(id)

				for scanr.Scan() {

					line := scanr.Text()
					frst, scnd := SplitInTwoAt(line, "\t", LEFT)
					frst = strings.ToLower(frst)

					if id != frst {
						return
					}
					if !strings.HasSuffix(str, rgt) {
						return
					}

					lft := strings.TrimSuffix(str, rgt)
					str = lft + "  " + scnd + "\n" + rgt

					if hd != "" {
						os.Stdout.WriteString(hd)
						os.Stdout.WriteString("\n")
					}

					os.Stdout.WriteString(str[:])
					os.Stdout.WriteString("\n")

					if tl != "" {
						os.Stdout.WriteString(tl)
						os.Stdout.WriteString("\n")
					}

					break
				}
			})

		if tail != "" {
			os.Stdout.WriteString(tail)
			os.Stdout.WriteString("\n")
		}

		fl.Close()

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// SORT XML RECORDS BY IDENTIFIER

	// -pattern record_name -sort parent/element@attribute^version
	if len(args) == 4 && args[2] == "-sort" {

		indx := args[3]

		// create map that records each UID
		order := make(map[string][]string)

		find := ParseIndex(indx)

		PartitionPattern(topPattern, star, rdr,
			func(str string) {
				recordCount++

				id := FindIdentifier(str[:], parent, find)
				if id == "" {
					return
				}

				data, ok := order[id]
				if !ok {
					data = make([]string, 0, 1)
				}
				data = append(data, str)
				// always need to update order, since data may be reallocated
				order[id] = data
			})

		var keys []string
		for ky := range order {
			keys = append(keys, ky)
		}
		// sort fields in alphabetical or numeric order
		sort.Slice(keys, func(i, j int) bool {
			// numeric sort on strings checks lengths first
			if IsAllDigits(keys[i]) && IsAllDigits(keys[j]) {
				lni := len(keys[i])
				lnj := len(keys[j])
				// shorter string is numerically less, assuming no leading zeros
				if lni < lnj {
					return true
				}
				if lni > lnj {
					return false
				}
			}
			// same length or non-numeric, can now do string comparison on contents
			return keys[i] < keys[j]
		})

		if head != "" {
			os.Stdout.WriteString(head)
			os.Stdout.WriteString("\n")
		}

		for _, id := range keys {

			strs := order[id]
			for _, str := range strs {
				os.Stdout.WriteString(str)
				os.Stdout.WriteString("\n")
			}
		}

		if tail != "" {
			os.Stdout.WriteString(tail)
			os.Stdout.WriteString("\n")
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// SPLIT FILE BY BY RECORD COUNT

	// split XML record into subfiles by count
	if len(args) == 8 && args[2] == "-split" && args[4] == "-prefix" && args[6] == "-suffix" {

		// e.g., -head "<IdxDocumentSet>" -tail "</IdxDocumentSet>" -pattern IdxDocument -split 250000 -prefix "biocon" -suffix "e2x"
		count := 0
		fnum := 0
		var (
			fl  *os.File
			err error
		)
		chunk, err := strconv.Atoi(args[3])
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s\n", err.Error())
			return
		}
		prefix := args[5]
		suffix := args[7]

		PartitionPattern(topPattern, star, rdr,
			func(str string) {
				recordCount++

				if count >= chunk {
					if tail != "" {
						fl.WriteString(tail)
						fl.WriteString("\n")
					}
					fl.Close()
					count = 0
				}
				if count == 0 {
					fpath := fmt.Sprintf("%s%03d.%s", prefix, fnum, suffix)
					fl, err = os.Create(fpath)
					if err != nil {
						fmt.Fprintf(os.Stderr, "%s\n", err.Error())
						return
					}
					os.Stderr.WriteString(fpath + "\n")
					fnum++
					if head != "" {
						fl.WriteString(head)
						fl.WriteString("\n")
					}
				}
				count++

				fl.WriteString(str[:])
				fl.WriteString("\n")
			})

		if count >= chunk {
			if tail != "" {
				fl.WriteString(tail)
				fl.WriteString("\n")
			}
			fl.Close()
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// CONCURRENT REFORMATTING OF PARSED XML RECORDS

	// -pattern plus -format does concurrent flush reformatting
	if len(args) > 2 && args[2] == "-format" {

		xmlq := CreateProducer(topPattern, star, rdr)
		fchq := CreateFormatters(topPattern, xmlq)
		unsq := CreateUnshuffler(fchq)

		if xmlq == nil || fchq == nil || unsq == nil {
			fmt.Fprintf(os.Stderr, "\nERROR: Unable to create formatter\n")
			os.Exit(1)
		}

		if head != "" {
			os.Stdout.WriteString(head)
			os.Stdout.WriteString("\n")
		}

		// drain output channel
		for curr := range unsq {

			str := curr.Text

			if str == "" {
				continue
			}

			if hd != "" {
				os.Stdout.WriteString(hd)
				os.Stdout.WriteString("\n")
			}

			// send result to output
			os.Stdout.WriteString(str)
			if !strings.HasSuffix(str, "\n") {
				os.Stdout.WriteString("\n")
			}

			if tl != "" {
				os.Stdout.WriteString(tl)
				os.Stdout.WriteString("\n")
			}

			recordCount++
			runtime.Gosched()
		}

		if tail != "" {
			os.Stdout.WriteString(tail)
			os.Stdout.WriteString("\n")
		}

		debug.FreeOSMemory()

		if timr {
			printDuration("records")
		}

		return
	}

	// PARSE AND VALIDATE EXTRACTION ARGUMENTS

	// parse nested exploration instruction from command-line arguments
	cmds := ParseArguments(args, topPattern)
	if cmds == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Problem parsing command-line arguments\n")
		os.Exit(1)
	}

	// GLOBAL MAP FOR SORT-UNIQ-COUNT HISTOGRAM ARGUMENT

	histogram := make(map[string]int)

	// PERFORMANCE TIMING COMMAND

	// -stats with an extraction command prints XML size and processing time for each record
	if stts {

		legend := "REC\tOFST\tSIZE\tTIME"

		rec := 0

		PartitionPattern(topPattern, star, rdr,
			func(str string) {
				rec++
				beginTime := time.Now()
				ProcessQuery(str[:], parent, rec, hd, tl, transform, histogram, cmds)
				endTime := time.Now()
				duration := endTime.Sub(beginTime)
				micro := int(float64(duration.Nanoseconds()) / 1e3)
				if legend != "" {
					fmt.Printf("%s\n", legend)
					legend = ""
				}
				fmt.Printf("%d\t%d\t%d\n", rec, len(str), micro)
			})

		return
	}

	// PERFORMANCE OPTIMIZATION FUNCTION

	// -trial -input fileName runs the specified extraction for each -proc from 1 to nCPU
	if trial && fileName != "" {

		legend := "CPU\tRATE\tDEV"

		for numServ := 1; numServ <= ncpu; numServ++ {

			NumServe = numServ

			runtime.GOMAXPROCS(numServ)

			sum := 0
			count := 0
			mean := 0.0
			m2 := 0.0

			// calculate mean and standard deviation of processing rate
			for trials := 0; trials < 5; trials++ {

				inFile, err := os.Open(fileName)
				if err != nil {
					fmt.Fprintf(os.Stderr, "\nERROR: Unable to open input file '%s'\n", fileName)
					os.Exit(1)
				}

				trdr := CreateReader(inFile)
				if trdr == nil {
					fmt.Fprintf(os.Stderr, "\nERROR: Unable to read input file\n")
					os.Exit(1)
				}

				xmlq := CreateProducer(topPattern, star, trdr)
				tblq := CreateConsumers(cmds, parent, hd, tl, transform, histogram, xmlq)

				if xmlq == nil || tblq == nil {
					fmt.Fprintf(os.Stderr, "\nERROR: Unable to create servers\n")
					os.Exit(1)
				}

				begTime := time.Now()
				recordCount = 0

				for range tblq {
					recordCount++
					runtime.Gosched()
				}

				inFile.Close()

				debug.FreeOSMemory()

				endTime := time.Now()
				expended := endTime.Sub(begTime)
				secs := float64(expended.Nanoseconds()) / 1e9

				if secs >= 0.000001 && recordCount > 0 {
					speed := int(float64(recordCount) / secs)
					sum += speed
					count++
					x := float64(speed)
					delta := x - mean
					mean += delta / float64(count)
					m2 += delta * (x - mean)
				}
			}

			if legend != "" {
				fmt.Printf("%s\n", legend)
				legend = ""
			}
			if count > 1 {
				vrc := m2 / float64(count-1)
				dev := int(math.Sqrt(vrc))
				fmt.Printf("%d\t%d\t%d\n", numServ, sum/count, dev)
			}
		}

		return
	}

	// PROCESS SINGLE SELECTED RECORD IF -pattern ARGUMENT IS IMMEDIATELY FOLLOWED BY -position COMMAND

	posn := ""
	if cmds.Visit == topPat {
		if cmds.Position == "outer" ||
			cmds.Position == "inner" ||
			cmds.Position == "even" ||
			cmds.Position == "odd" ||
			cmds.Position == "all" {
			// filter by record position when draining unshuffler channel
			posn = cmds.Position
			cmds.Position = ""
		}
	}

	if cmds.Visit == topPat && cmds.Position != "" && cmds.Position != "select" {

		qry := ""
		idx := 0
		rec := 0

		if cmds.Position == "first" {

			PartitionPattern(topPattern, star, rdr,
				func(str string) {
					rec++
					if rec == 1 {
						qry = str
						idx = rec
					}
				})

		} else if cmds.Position == "last" {

			PartitionPattern(topPattern, star, rdr,
				func(str string) {
					qry = str
					idx = rec
				})

		} else {

			// use numeric position
			number, err := strconv.Atoi(cmds.Position)
			if err != nil {
				fmt.Fprintf(os.Stderr, "\nERROR: Unrecognized position '%s'\n", cmds.Position)
				os.Exit(1)
			}

			PartitionPattern(topPattern, star, rdr,
				func(str string) {
					rec++
					if rec == number {
						qry = str
						idx = rec
					}
				})
		}

		if qry == "" {
			return
		}

		// clear position on top node to prevent condition test failure
		cmds.Position = ""

		// process single selected record
		res := ProcessQuery(qry[:], parent, idx, hd, tl, transform, histogram, cmds)

		if res != "" {
			fmt.Printf("%s", res)
		}

		return
	}

	// LAUNCH PRODUCER, CONSUMER, AND UNSHUFFLER SERVERS

	// launch producer goroutine to partition XML by pattern
	xmlq := CreateProducer(topPattern, star, rdr)

	// launch consumer goroutines to parse and explore partitioned XML objects
	tblq := CreateConsumers(cmds, parent, hd, tl, transform, histogram, xmlq)

	// launch unshuffler goroutine to restore order of results
	unsq := CreateUnshuffler(tblq)

	if xmlq == nil || tblq == nil || unsq == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create servers\n")
		os.Exit(1)
	}

	// PERFORMANCE SUMMARY

	if dbug {

		// drain results, but suppress extraction output
		for ext := range unsq {
			byteCount += len(ext.Text)
			recordCount++
			runtime.Gosched()
		}

		// force garbage collection, return memory to operating system
		debug.FreeOSMemory()

		// print processing parameters as XML object
		stopTime := time.Now()
		duration := stopTime.Sub(StartTime)
		seconds := float64(duration.Nanoseconds()) / 1e9

		// Threads is a more easily explained concept than GOMAXPROCS
		fmt.Printf("<Xtract>\n")
		fmt.Printf("  <Threads>%d</Threads>\n", numProcs)
		fmt.Printf("  <Parsers>%d</Parsers>\n", NumServe)
		fmt.Printf("  <Time>%.3f</Time>\n", seconds)
		if seconds >= 0.001 && recordCount > 0 {
			rate := int(float64(recordCount) / seconds)
			fmt.Printf("  <Rate>%d</Rate>\n", rate)
		}
		fmt.Printf("</Xtract>\n")

		return
	}

	// DRAIN OUTPUT CHANNEL TO EXECUTE EXTRACTION COMMANDS, RESTORE OUTPUT ORDER WITH HEAP

	var buffer strings.Builder
	count := 0
	okay := false

	wrtr := bufio.NewWriter(os.Stdout)

	// printResult prints output for current pattern, handles -empty and -ident flags, and periodically flushes buffer
	printResult := func(curr Extract) {

		str := curr.Text

		if mpty {

			if str == "" {

				okay = true

				idx := curr.Index
				val := strconv.Itoa(idx)
				buffer.WriteString(val[:])
				buffer.WriteString("\n")

				count++
			}

		} else if str != "" {

			okay = true

			if idnt {
				idx := curr.Index
				val := strconv.Itoa(idx)
				buffer.WriteString(val[:])
				buffer.WriteString("\t")
			}

			// save output to byte buffer
			buffer.WriteString(str[:])

			count++
		}

		if count > 1000 {
			count = 0
			txt := buffer.String()
			if txt != "" {
				// print current buffer
				wrtr.WriteString(txt[:])
			}
			buffer.Reset()
		}
	}

	if head != "" {
		buffer.WriteString(head[:])
		buffer.WriteString("\n")
	}

	// drain unshuffler channel

	if posn == "outer" {

		// print only first and last records
		var beg *Extract
		var end *Extract

		for curr := range unsq {

			if beg == nil {
				beg = &Extract{curr.Index, curr.Ident, curr.Text, nil}
			} else {
				end = &Extract{curr.Index, curr.Ident, curr.Text, nil}
			}

			recordCount++
		}

		if beg != nil {
			printResult(*beg)
		}
		if end != nil {
			printResult(*end)
		}

	} else if posn == "inner" {

		// print all but first and last records
		var prev *Extract
		var next *Extract
		first := true

		for curr := range unsq {

			if first {
				first = false
			} else {
				prev = next
				next = &Extract{curr.Index, curr.Ident, curr.Text, nil}
			}

			if prev != nil {
				printResult(*prev)
			}

			recordCount++
		}

	} else if posn == "even" {

		even := false

		for curr := range unsq {

			if even {
				printResult(curr)
			}
			even = !even

			recordCount++
		}

	} else if posn == "odd" {

		odd := true

		for curr := range unsq {

			if odd {
				printResult(curr)
			}
			odd = !odd

			recordCount++
		}

	} else {

		// default or -position all
		for curr := range unsq {

			// send result to output
			printResult(curr)

			recordCount++
			runtime.Gosched()
		}
	}

	if tail != "" {
		buffer.WriteString(tail[:])
		buffer.WriteString("\n")
	}

	// do not print head or tail if no extraction output
	if okay {
		txt := buffer.String()
		if txt != "" {
			// print final buffer
			wrtr.WriteString(txt[:])
		}
	}
	buffer.Reset()

	wrtr.Flush()

	// print -histogram results, if populated
	var keys []string
	for ky := range histogram {
		keys = append(keys, ky)
	}
	if len(keys) > 0 {
		// sort fields in alphabetical or numeric order
		sort.Slice(keys, func(i, j int) bool {
			// numeric sort on strings checks lengths first
			if IsAllDigits(keys[i]) && IsAllDigits(keys[j]) {
				lni := len(keys[i])
				lnj := len(keys[j])
				// shorter string is numerically less, assuming no leading zeros
				if lni < lnj {
					return true
				}
				if lni > lnj {
					return false
				}
			}
			// same length or non-numeric, can now do string comparison on contents
			return keys[i] < keys[j]
		})

		for _, str := range keys {

			count := histogram[str]
			val := strconv.Itoa(count)
			os.Stdout.WriteString(val)
			os.Stdout.WriteString("\t")
			os.Stdout.WriteString(str)
			os.Stdout.WriteString("\n")
		}
	}

	// force garbage collection and return memory before calculating processing rate
	debug.FreeOSMemory()

	if timr {
		printDuration("records")
	}
}
