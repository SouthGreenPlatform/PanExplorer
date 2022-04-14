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
// File Name:  common.go
//
// Author:  Jonathan Kans
//
// ==========================================================================

/*
  Older - Download external Go libraries by running:

  cd "$GOPATH"
  go get -u github.com/fatih/color
  go get -u github.com/fiam/gounidecode/unidecode
  go get -u github.com/gedex/inflector
  go get -u github.com/klauspost/cpuid
  go get -u github.com/pbnjay/memory
  go get -u github.com/surgebase/porter2
  go get -u golang.org/x/text/runes
  go get -u golang.org/x/text/transform
  go get -u golang.org/x/text/unicode/norm

  Newer - Prepare modules by running:

  cd edirect
  go mod init edirect
  go mod tidy

  Test for presence of Go compiler, and cross-compile xtract executable, by running:

  if hash go 2>/dev/null
  then
    mods="darwin amd64 Darwin linux amd64 Linux windows 386 CYGWIN_NT linux arm ARM"

    echo "$mods" |
    xargs -n 3 sh -c 'env GOOS="$0" GOARCH="$1" go build -o xtract."$2" xtract.go common.go'

    echo "$mods" |
    xargs -n 3 sh -c 'env GOOS="$0" GOARCH="$1" go build -o rchive."$2" rchive.go common.go'
  fi
*/

package main

import (
	"bytes"
	"container/heap"
	"fmt"
	"golang.org/x/text/runes"
	"golang.org/x/text/transform"
	"golang.org/x/text/unicode/norm"
	"io"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
)

// TYPED CONSTANTS

type SideType int

const (
	_ SideType = iota
	LEFT
	RIGHT
)

type TagType int

const (
	NOTAG TagType = iota
	STARTTAG
	SELFTAG
	STOPTAG
	ATTRIBTAG
	CONTENTTAG
	CDATATAG
	COMMENTTAG
	DOCTYPETAG
	OBJECTTAG
	CONTAINERTAG
	ISCLOSED
	BADTAG
)

type ContentType int

const (
	NONE  ContentType = iota
	MIXED             = 1 << iota
	AMPER
	ASCII
	LFTSPACE
	RGTSPACE
)

type VerifyType int

const (
	_ VerifyType = iota
	START
	STOP
	CHAR
	OTHER
)

// ARGUMENT MAPS

var scriptRunes = map[rune]rune{
	'\u00B2': '2',
	'\u00B3': '3',
	'\u00B9': '1',
	'\u2070': '0',
	'\u2071': '1',
	'\u2074': '4',
	'\u2075': '5',
	'\u2076': '6',
	'\u2077': '7',
	'\u2078': '8',
	'\u2079': '9',
	'\u207A': '+',
	'\u207B': '-',
	'\u207C': '=',
	'\u207D': '(',
	'\u207E': ')',
	'\u207F': 'n',
	'\u2080': '0',
	'\u2081': '1',
	'\u2082': '2',
	'\u2083': '3',
	'\u2084': '4',
	'\u2085': '5',
	'\u2086': '6',
	'\u2087': '7',
	'\u2088': '8',
	'\u2089': '9',
	'\u208A': '+',
	'\u208B': '-',
	'\u208C': '=',
	'\u208D': '(',
	'\u208E': ')',
}

var accentRunes = map[rune]rune{
	'\u00D8': 'O',
	'\u00F0': 'd',
	'\u00F8': 'o',
	'\u0111': 'd',
	'\u0131': 'i',
	'\u0141': 'L',
	'\u0142': 'l',
	'\u02BC': '\'',
}

var ligatureRunes = map[rune]string{
	'\u00DF': "ss",
	'\u00E6': "ae",
	'\uFB00': "ff",
	'\uFB01': "fi",
	'\uFB02': "fl",
	'\uFB03': "ffi",
	'\uFB04': "ffl",
	'\uFB05': "ft",
	'\uFB06': "st",
}

var greekRunes = map[rune]string{
	'\u0190': "epsilon",
	'\u025B': "epsilon",
	'\u03B1': "alpha",
	'\u03B2': "beta",
	'\u03B3': "gamma",
	'\u03B4': "delta",
	'\u03B5': "epsilon",
	'\u03B6': "zeta",
	'\u03B7': "eta",
	'\u03B8': "theta",
	'\u03B9': "iota",
	'\u03BA': "kappa",
	'\u03BB': "lambda",
	'\u03BC': "mu",
	'\u03BD': "nu",
	'\u03BE': "xi",
	'\u03BF': "omicron",
	'\u03C0': "pi",
	'\u03C1': "rho",
	'\u03C3': "sigma",
	'\u03C4': "tau",
	'\u03C5': "upsilon",
	'\u03C6': "phi",
	'\u03C7': "chi",
	'\u03C8': "psi",
	'\u03C9': "omega",
	'\u0391': "alpha",
	'\u0392': "beta",
	'\u0393': "gamma",
	'\u0394': "delta",
	'\u0395': "epsilon",
	'\u0396': "zeta",
	'\u0397': "eta",
	'\u0398': "theta",
	'\u0399': "iota",
	'\u039A': "kappa",
	'\u039B': "lambda",
	'\u039C': "mu",
	'\u039D': "nu",
	'\u039E': "xi",
	'\u039F': "omicron",
	'\u03A0': "pi",
	'\u03A1': "rho",
	'\u03A3': "sigma",
	'\u03A4': "tau",
	'\u03A5': "upsilon",
	'\u03A6': "phi",
	'\u03A7': "chi",
	'\u03A8': "psi",
	'\u03A9': "omega",
	'\u03D1': "theta",
	'\u03D5': "phi",
	'\u03D6': "pi",
	'\u03F0': "kappa",
	'\u03F1': "rho",
	'\u03F5': "epsilon",
}

var isStopWord = map[string]bool{
	"a":             true,
	"about":         true,
	"above":         true,
	"abs":           true,
	"accordingly":   true,
	"across":        true,
	"after":         true,
	"afterwards":    true,
	"again":         true,
	"against":       true,
	"all":           true,
	"almost":        true,
	"alone":         true,
	"along":         true,
	"already":       true,
	"also":          true,
	"although":      true,
	"always":        true,
	"am":            true,
	"among":         true,
	"amongst":       true,
	"an":            true,
	"analyze":       true,
	"and":           true,
	"another":       true,
	"any":           true,
	"anyhow":        true,
	"anyone":        true,
	"anything":      true,
	"anywhere":      true,
	"applicable":    true,
	"apply":         true,
	"are":           true,
	"arise":         true,
	"around":        true,
	"as":            true,
	"assume":        true,
	"at":            true,
	"be":            true,
	"became":        true,
	"because":       true,
	"become":        true,
	"becomes":       true,
	"becoming":      true,
	"been":          true,
	"before":        true,
	"beforehand":    true,
	"being":         true,
	"below":         true,
	"beside":        true,
	"besides":       true,
	"between":       true,
	"beyond":        true,
	"both":          true,
	"but":           true,
	"by":            true,
	"came":          true,
	"can":           true,
	"cannot":        true,
	"cc":            true,
	"cm":            true,
	"come":          true,
	"compare":       true,
	"could":         true,
	"de":            true,
	"dealing":       true,
	"department":    true,
	"depend":        true,
	"did":           true,
	"discover":      true,
	"dl":            true,
	"do":            true,
	"does":          true,
	"done":          true,
	"due":           true,
	"during":        true,
	"each":          true,
	"ec":            true,
	"ed":            true,
	"effected":      true,
	"eg":            true,
	"either":        true,
	"else":          true,
	"elsewhere":     true,
	"enough":        true,
	"especially":    true,
	"et":            true,
	"etc":           true,
	"ever":          true,
	"every":         true,
	"everyone":      true,
	"everything":    true,
	"everywhere":    true,
	"except":        true,
	"find":          true,
	"for":           true,
	"found":         true,
	"from":          true,
	"further":       true,
	"gave":          true,
	"get":           true,
	"give":          true,
	"go":            true,
	"gone":          true,
	"got":           true,
	"gov":           true,
	"had":           true,
	"has":           true,
	"have":          true,
	"having":        true,
	"he":            true,
	"hence":         true,
	"her":           true,
	"here":          true,
	"hereafter":     true,
	"hereby":        true,
	"herein":        true,
	"hereupon":      true,
	"hers":          true,
	"herself":       true,
	"him":           true,
	"himself":       true,
	"his":           true,
	"how":           true,
	"however":       true,
	"hr":            true,
	"i":             true,
	"ie":            true,
	"if":            true,
	"ii":            true,
	"iii":           true,
	"immediately":   true,
	"importance":    true,
	"important":     true,
	"in":            true,
	"inc":           true,
	"incl":          true,
	"indeed":        true,
	"into":          true,
	"investigate":   true,
	"is":            true,
	"it":            true,
	"its":           true,
	"itself":        true,
	"just":          true,
	"keep":          true,
	"kept":          true,
	"kg":            true,
	"km":            true,
	"last":          true,
	"latter":        true,
	"latterly":      true,
	"lb":            true,
	"ld":            true,
	"letter":        true,
	"like":          true,
	"ltd":           true,
	"made":          true,
	"mainly":        true,
	"make":          true,
	"many":          true,
	"may":           true,
	"me":            true,
	"meanwhile":     true,
	"mg":            true,
	"might":         true,
	"ml":            true,
	"mm":            true,
	"mo":            true,
	"more":          true,
	"moreover":      true,
	"most":          true,
	"mostly":        true,
	"mr":            true,
	"much":          true,
	"mug":           true,
	"must":          true,
	"my":            true,
	"myself":        true,
	"namely":        true,
	"nearly":        true,
	"necessarily":   true,
	"neither":       true,
	"never":         true,
	"nevertheless":  true,
	"next":          true,
	"no":            true,
	"nobody":        true,
	"noone":         true,
	"nor":           true,
	"normally":      true,
	"nos":           true,
	"not":           true,
	"noted":         true,
	"nothing":       true,
	"now":           true,
	"nowhere":       true,
	"obtained":      true,
	"of":            true,
	"off":           true,
	"often":         true,
	"on":            true,
	"only":          true,
	"onto":          true,
	"or":            true,
	"other":         true,
	"others":        true,
	"otherwise":     true,
	"ought":         true,
	"our":           true,
	"ours":          true,
	"ourselves":     true,
	"out":           true,
	"over":          true,
	"overall":       true,
	"owing":         true,
	"own":           true,
	"oz":            true,
	"particularly":  true,
	"per":           true,
	"perhaps":       true,
	"pm":            true,
	"pmid":          true,
	"precede":       true,
	"predominantly": true,
	"present":       true,
	"presently":     true,
	"previously":    true,
	"primarily":     true,
	"promptly":      true,
	"pt":            true,
	"quickly":       true,
	"quite":         true,
	"quot":          true,
	"rather":        true,
	"readily":       true,
	"really":        true,
	"recently":      true,
	"refs":          true,
	"regarding":     true,
	"relate":        true,
	"said":          true,
	"same":          true,
	"seem":          true,
	"seemed":        true,
	"seeming":       true,
	"seems":         true,
	"seen":          true,
	"seriously":     true,
	"several":       true,
	"shall":         true,
	"she":           true,
	"should":        true,
	"show":          true,
	"showed":        true,
	"shown":         true,
	"shows":         true,
	"significantly": true,
	"since":         true,
	"slightly":      true,
	"so":            true,
	"some":          true,
	"somehow":       true,
	"someone":       true,
	"something":     true,
	"sometime":      true,
	"sometimes":     true,
	"somewhat":      true,
	"somewhere":     true,
	"soon":          true,
	"specifically":  true,
	"still":         true,
	"strongly":      true,
	"studied":       true,
	"studies":       true,
	"study":         true,
	"sub":           true,
	"substantially": true,
	"such":          true,
	"sufficiently":  true,
	"take":          true,
	"tell":          true,
	"th":            true,
	"than":          true,
	"that":          true,
	"the":           true,
	"their":         true,
	"theirs":        true,
	"them":          true,
	"themselves":    true,
	"then":          true,
	"thence":        true,
	"there":         true,
	"thereafter":    true,
	"thereby":       true,
	"therefore":     true,
	"therein":       true,
	"thereupon":     true,
	"these":         true,
	"they":          true,
	"this":          true,
	"thorough":      true,
	"those":         true,
	"though":        true,
	"through":       true,
	"throughout":    true,
	"thru":          true,
	"thus":          true,
	"to":            true,
	"together":      true,
	"too":           true,
	"toward":        true,
	"towards":       true,
	"try":           true,
	"type":          true,
	"ug":            true,
	"under":         true,
	"unless":        true,
	"until":         true,
	"up":            true,
	"upon":          true,
	"us":            true,
	"use":           true,
	"used":          true,
	"usefully":      true,
	"usefulness":    true,
	"using":         true,
	"usually":       true,
	"various":       true,
	"very":          true,
	"via":           true,
	"was":           true,
	"we":            true,
	"were":          true,
	"what":          true,
	"whatever":      true,
	"when":          true,
	"whence":        true,
	"whenever":      true,
	"where":         true,
	"whereafter":    true,
	"whereas":       true,
	"whereby":       true,
	"wherein":       true,
	"whereupon":     true,
	"wherever":      true,
	"whether":       true,
	"which":         true,
	"while":         true,
	"whither":       true,
	"who":           true,
	"whoever":       true,
	"whom":          true,
	"whose":         true,
	"why":           true,
	"will":          true,
	"with":          true,
	"within":        true,
	"without":       true,
	"wk":            true,
	"would":         true,
	"wt":            true,
	"yet":           true,
	"you":           true,
	"your":          true,
	"yours":         true,
	"yourself":      true,
	"yourselves":    true,
	"yr":            true,
}

var htmlRepair = map[string]string{
	"&amp;lt;b&amp;gt;":     "<b>",
	"&amp;lt;i&amp;gt;":     "<i>",
	"&amp;lt;u&amp;gt;":     "<u>",
	"&amp;lt;/b&amp;gt;":    "</b>",
	"&amp;lt;/i&amp;gt;":    "</i>",
	"&amp;lt;/u&amp;gt;":    "</u>",
	"&amp;lt;b/&amp;gt;":    "<b/>",
	"&amp;lt;i/&amp;gt;":    "<i/>",
	"&amp;lt;u/&amp;gt;":    "<u/>",
	"&amp;lt;b /&amp;gt;":   "<b/>",
	"&amp;lt;i /&amp;gt;":   "<i/>",
	"&amp;lt;u /&amp;gt;":   "<u/>",
	"&amp;lt;sub&amp;gt;":   "<sub>",
	"&amp;lt;sup&amp;gt;":   "<sup>",
	"&amp;lt;/sub&amp;gt;":  "</sub>",
	"&amp;lt;/sup&amp;gt;":  "</sup>",
	"&amp;lt;sub/&amp;gt;":  "<sub/>",
	"&amp;lt;sup/&amp;gt;":  "<sup/>",
	"&amp;lt;sub /&amp;gt;": "<sub/>",
	"&amp;lt;sup /&amp;gt;": "<sup/>",
	"&lt;b&gt;":             "<b>",
	"&lt;i&gt;":             "<i>",
	"&lt;u&gt;":             "<u>",
	"&lt;/b&gt;":            "</b>",
	"&lt;/i&gt;":            "</i>",
	"&lt;/u&gt;":            "</u>",
	"&lt;b/&gt;":            "<b/>",
	"&lt;i/&gt;":            "<i/>",
	"&lt;u/&gt;":            "<u/>",
	"&lt;b /&gt;":           "<b/>",
	"&lt;i /&gt;":           "<i/>",
	"&lt;u /&gt;":           "<u/>",
	"&lt;sub&gt;":           "<sub>",
	"&lt;sup&gt;":           "<sup>",
	"&lt;/sub&gt;":          "</sub>",
	"&lt;/sup&gt;":          "</sup>",
	"&lt;sub/&gt;":          "<sub/>",
	"&lt;sup/&gt;":          "<sup/>",
	"&lt;sub /&gt;":         "<sub/>",
	"&lt;sup /&gt;":         "<sup/>",
}

var hyphenatedPrefixes = map[string]bool{
	"anti":    true,
	"bi":      true,
	"co":      true,
	"contra":  true,
	"counter": true,
	"de":      true,
	"di":      true,
	"extra":   true,
	"infra":   true,
	"inter":   true,
	"intra":   true,
	"micro":   true,
	"mid":     true,
	"mono":    true,
	"multi":   true,
	"non":     true,
	"over":    true,
	"peri":    true,
	"post":    true,
	"pre":     true,
	"pro":     true,
	"proto":   true,
	"pseudo":  true,
	"re":      true,
	"semi":    true,
	"sub":     true,
	"super":   true,
	"supra":   true,
	"tetra":   true,
	"trans":   true,
	"tri":     true,
	"ultra":   true,
	"un":      true,
	"under":   true,
	"whole":   true,
}

var primedPrefixes = map[string]bool{
	"5": true,
	"3": true,
}

var primedSuffix = map[string]bool{
	"s": true,
}

// DATA OBJECTS

type Node struct {
	Name       string
	Parent     string
	Contents   string
	Attributes string
	Attribs    []string
	Children   *Node
	Next       *Node
}

type Find struct {
	Index  string
	Parent string
	Match  string
	Attrib string
	Versn  string
}

type Token struct {
	Tag   TagType
	Cont  ContentType
	Name  string
	Attr  string
	Index int
	Line  int
}

type MarkupType int

const (
	NOSCRIPT MarkupType = iota
	SUPSCRIPT
	SUBSCRIPT
	PLAINDIGIT
)

type MarkupPolicy int

const (
	NOMARKUP MarkupPolicy = iota
	FUSE
	SPACE
	PERIOD
	BRACKETS
	MARKDOWN
	SLASH
	TAGS
	TERSE
)

// GLOBAL VARIABLES

var (
	InBlank   [256]bool
	InFirst   [256]bool
	InElement [256]bool
	InLower   [256]bool
	InContent [256]bool

	ChanDepth int
	FarmSize  int
	HeapSize  int
	NumServe  int

	DoCompress  bool
	DoCleanup   bool
	DoStrict    bool
	DoMixed     bool
	DoUnicode   bool
	DoScript    bool
	DoMathML    bool
	DeAccent    bool
	DoASCII     bool
	DoStem      bool
	DeStop      bool
	AllowEmbed  bool
	ContentMods bool
	CountLines  bool

	UnicodeFix = NOMARKUP
	ScriptFix  = NOMARKUP
	MathMLFix  = NOMARKUP

	IdxFields []string

	StartTime time.Time
)

// UTILITIES

func CleanupBadSpaces(str string) string {

	var buffer strings.Builder

	for _, ch := range str {
		if ch > 127 && unicode.IsSpace(ch) {
			buffer.WriteRune(' ')
		} else {
			buffer.WriteRune(ch)
		}
	}

	return buffer.String()
}

func CleanupContents(str string, ascii, amper, mixed bool) string {

	if DoCompress {
		if !AllowEmbed {
			if ascii && HasBadSpace(str) {
				str = CleanupBadSpaces(str)
			}
		}
		if HasAdjacentSpacesOrNewline(str) {
			str = CompressRunsOfSpaces(str)
		}
	}
	if DoUnicode {
		if ascii && HasUnicodeMarkup(str) {
			str = RepairUnicodeMarkup(str, UnicodeFix)
		}
	}
	if AllowEmbed {
		if amper {
			str = RepairEncodedMarkup(str)
		}
	}
	if DoScript {
		if mixed && HasAngleBracket(str) {
			str = RepairScriptMarkup(str, ScriptFix)
		}
	}
	if DoMathML {
		if mixed && HasAngleBracket(str) {
			str = RepairMathMLMarkup(str, MathMLFix)
		}
	}
	if DoStrict {
		if mixed || amper {
			if HasAngleBracket(str) {
				str = RepairTableMarkup(str, SPACE)
				str = RemoveEmbeddedMarkup(str)
			}
		}
		if ascii && HasBadSpace(str) {
			str = CleanupBadSpaces(str)
		}
		if HasAdjacentSpaces(str) {
			str = CompressRunsOfSpaces(str)
		}
		// Remove MathML artifact
		if NeedsTightening(str) {
			str = TightenParentheses(str)
		}
	}
	if DoMixed {
		if mixed {
			str = DoTrimFlankingHTML(str)
		}
		if ascii && HasBadSpace(str) {
			str = CleanupBadSpaces(str)
		}
		if HasAdjacentSpaces(str) {
			str = CompressRunsOfSpaces(str)
		}
	}
	if DeAccent {
		if ascii {
			str = DoAccentTransform(str)
		}
	}
	if DoASCII {
		if ascii {
			str = UnicodeToASCII(str)
		}
	}

	if HasFlankingSpace(str) {
		str = strings.TrimSpace(str)
	}

	return str
}

func CompressRunsOfSpaces(str string) string {

	whiteSpace := false
	var buffer strings.Builder

	for _, ch := range str {
		if ch < 127 && InBlank[ch] {
			if !whiteSpace {
				buffer.WriteRune(' ')
			}
			whiteSpace = true
		} else {
			buffer.WriteRune(ch)
			whiteSpace = false
		}
	}

	return buffer.String()
}

func ConvertSlash(str string) string {

	if str == "" {
		return str
	}

	length := len(str)
	res := make([]byte, length+1, length+1)

	isSlash := false
	idx := 0
	for _, ch := range str {
		if isSlash {
			switch ch {
			case 'n':
				// line feed
				res[idx] = '\n'
			case 'r':
				// carriage return
				res[idx] = '\r'
			case 't':
				// horizontal tab
				res[idx] = '\t'
			case 'f':
				// form feed
				res[idx] = '\f'
			case 'a':
				// audible bell from terminal (undocumented)
				res[idx] = '\x07'
			default:
				res[idx] = byte(ch)
			}
			idx++
			isSlash = false
		} else if ch == '\\' {
			isSlash = true
		} else {
			res[idx] = byte(ch)
			idx++
		}
	}

	res = res[0:idx]

	return string(res)
}

var (
	rlock sync.Mutex
	ffix  *strings.Replacer
)

func DecodeFields(str string) string {

	// NewReplacer not reentrant (?), protected by mutex
	rlock.Lock()

	if ffix == nil {
		// handles bracketed field specifiers
		ffix = strings.NewReplacer(
			"[chem]", " CHEM ",
			"[code]", " CODE ",
			"[conv]", " CONV ",
			"[disz]", " DISZ ",
			"[gene]", " GENE ",
			"[norm]", " NORM ",
			"[path]", " PATH ",
			"[pipe]", " PIPE ",
			"[stem]", " STEM ",
			"[thme]", " THME ",
			"[tree]", " TREE ",
			"[year]", " YEAR ",
		)
	}

	// must do after lower casing and removing underscores, but before removing hyphens
	if ffix != nil {

		str = CompressRunsOfSpaces(str)
		str = strings.TrimSpace(str)

		str = " " + str + " "

		str = ffix.Replace(str)

		str = CompressRunsOfSpaces(str)
		str = strings.TrimSpace(str)
	}

	rlock.Unlock()

	return str
}

var (
	tlock sync.Mutex
	tform transform.Transformer
)

func DoAccentTransform(str string) string {

	// transformer not reentrant, protected by mutex
	tlock.Lock()

	if tform == nil {
		tform = transform.Chain(norm.NFD, runes.Remove(runes.In(unicode.Mn)), norm.NFC)
	}

	if tform != nil {

		var arry []string

		// split long string into words to avoid transform short internal buffer error
		terms := strings.Fields(str)

		for _, item := range terms {

			// remove accents from single word
			tmp, _, err := transform.String(tform, item)
			if err == nil {
				// collect transformed result
				arry = append(arry, tmp)
			} else {
				fmt.Fprintf(os.Stderr, "%s\n", err.Error())
			}
		}

		// reconstruct string from transformed words
		str = strings.Join(arry, " ")
	}

	// look for characters not in current external runes conversion table
	if HasBadAccent(str) {
		str = FixBadAccent(str)
	}

	tlock.Unlock()

	return str
}

func DoTrimFlankingHTML(str string) string {

	badPrefix := [10]string{
		"<i></i>",
		"<b></b>",
		"<u></u>",
		"<sup></sup>",
		"<sub></sub>",
		"</i>",
		"</b>",
		"</u>",
		"</sup>",
		"</sub>",
	}

	badSuffix := [10]string{
		"<i></i>",
		"<b></b>",
		"<u></u>",
		"<sup></sup>",
		"<sub></sub>",
		"<i>",
		"<b>",
		"<u>",
		"<sup>",
		"<sub>",
	}

	if strings.Contains(str, "<") {
		goOn := true
		for goOn {
			goOn = false
			for _, tag := range badPrefix {
				if strings.HasPrefix(str, tag) {
					str = str[len(tag):]
					goOn = true
				}
			}
			for _, tag := range badSuffix {
				if strings.HasSuffix(str, tag) {
					str = str[:len(str)-len(tag)]
					goOn = true
				}
			}
		}
	}

	return str
}

func FixBadAccent(str string) string {

	var buffer strings.Builder

	for _, ch := range str {
		if ch > 127 {
			if ch >= '\u00D8' && ch <= '\u02BC' {
				rn, ok := accentRunes[ch]
				if ok {
					buffer.WriteRune(rn)
					continue
				}
				st, ok := ligatureRunes[ch]
				if ok {
					buffer.WriteString(st)
					continue
				}
			}
			if ch >= '\uFB00' && ch <= '\uFB06' {
				st, ok := ligatureRunes[ch]
				if ok {
					buffer.WriteString(st)
					continue
				}
			}
		}
		buffer.WriteRune(ch)
	}

	return buffer.String()
}

func FixSpecialCases(str string) string {

	var arry []string
	var buffer strings.Builder

	terms := strings.Fields(str)

	for _, item := range terms {

		buffer.Reset()

		for i, ch := range item {
			if ch == '-' {
				_, ok := hyphenatedPrefixes[item[0:i]]
				if ok {
					continue
				}
			} else if ch == '\'' {
				_, ok := primedPrefixes[item[0:i]]
				if ok {
					buffer.WriteString("_prime ")
					continue
				}
				_, ok = primedSuffix[item[i:]]
				if ok {
					continue
				}
			}
			buffer.WriteRune(ch)
		}

		item = buffer.String()

		arry = append(arry, item)
	}

	// reconstruct string from transformed words
	str = strings.Join(arry, " ")

	return str
}

func FixThemeCases(str string) string {

	if !strings.Contains(str, "[thme]") && !strings.Contains(str, "[conv]") {
		return str
	}

	var arry []string

	terms := strings.Fields(str)

	for _, item := range terms {

		switch item {
		case "a+":
			arry = append(arry, "ap")
		case "e+":
			arry = append(arry, "ep")
		case "ec+":
			arry = append(arry, "ecp")
		case "eg+":
			arry = append(arry, "egp")
		case "v+":
			arry = append(arry, "vp")
		case "a-":
			arry = append(arry, "am")
		case "e-":
			arry = append(arry, "em")
		case "ec-":
			arry = append(arry, "ecm")
		default:
			arry = append(arry, item)
		}
	}

	// reconstruct string from transformed words
	str = strings.Join(arry, " ")

	return str
}

func FlattenMathML(str string, policy MarkupPolicy) string {

	findNextXMLBlock := func(txt string) (int, int, bool) {

		beg := strings.Index(txt, "<")
		if beg < 0 {
			return -1, -1, false
		}
		end := strings.Index(txt, ">")
		if end < 0 {
			return -1, -1, false
		}
		end++
		return beg, end, true
	}

	var arry []string

	for {
		beg, end, ok := findNextXMLBlock(str)
		if !ok {
			break
		}
		pfx := str[:beg]
		pfx = strings.TrimSpace(pfx)
		if pfx != "" {
			arry = append(arry, pfx)
		}
		tmp := str[beg:end]
		tmp = strings.TrimSpace(tmp)
		str = str[end:]
	}

	switch policy {
	case PERIOD:
	case SPACE:
		str = strings.Join(arry, " ")
	case BRACKETS:
	case MARKDOWN:
	case SLASH:
	case TAGS:
	case TERSE:
		str = strings.Join(arry, "")
	}

	str = strings.TrimSpace(str)

	// str = RemoveEmbeddedMarkup(str)

	return str
}

func HasAdjacentSpaces(str string) bool {

	whiteSpace := false

	for _, ch := range str {
		if ch == ' ' || ch == '\n' {
			if whiteSpace {
				return true
			}
			whiteSpace = true
		} else {
			whiteSpace = false
		}
	}

	return false
}

func HasAdjacentSpacesOrNewline(str string) bool {

	whiteSpace := false

	for _, ch := range str {
		if ch == '\n' {
			return true
		}
		if ch == ' ' {
			if whiteSpace {
				return true
			}
			whiteSpace = true
		} else {
			whiteSpace = false
		}
	}

	return false
}

func HasAmpOrNotASCII(str string) bool {

	for _, ch := range str {
		if ch == '&' || ch > 127 {
			return true
		}
	}

	return false
}

func HasAngleBracket(str string) bool {

	hasAmp := false
	hasSemi := false

	for _, ch := range str {
		if ch == '<' || ch == '>' {
			return true
		} else if ch == '&' {
			hasAmp = true
		} else if ch == ';' {
			hasSemi = true
		}
	}

	if hasAmp && hasSemi {
		if strings.Contains(str, "&lt;") ||
			strings.Contains(str, "&gt;") ||
			strings.Contains(str, "&amp;") {
			return true
		}
	}

	return false
}

func HasBadAccent(str string) bool {

	for _, ch := range str {
		if ch <= 127 {
			continue
		}
		// quick min-to-max check for additional characters to treat as accents
		if ch >= '\u00D8' && ch <= '\u02BC' {
			return true
		} else if ch >= '\uFB00' && ch <= '\uFB06' {
			return true
		}
	}

	return false
}

func HasBadSpace(str string) bool {

	for _, ch := range str {
		if ch > 127 && unicode.IsSpace(ch) {
			return true
		}
	}

	return false
}

func HasCommaOrSemicolon(str string) bool {

	for _, ch := range str {
		if ch == ',' || ch == ';' || ch == '-' {
			return true
		}
	}

	return false
}

func HasFlankingSpace(str string) bool {

	if str == "" {
		return false
	}

	ch := str[0]
	if ch < 127 && InBlank[ch] {
		return true
	}

	strlen := len(str)
	ch = str[strlen-1]
	if ch < 127 && InBlank[ch] {
		return true
	}

	return false
}

func HasGreek(str string) bool {

	for _, ch := range str {
		if ch <= 127 {
			continue
		}
		// quick min-to-max check for Greek characters to convert to english words
		if ch >= '\u03B1' && ch <= '\u03C9' {
			return true
		} else if ch >= '\u0391' && ch <= '\u03A9' {
			return true
		} else if ch >= '\u03D1' && ch <= '\u03D6' {
			return true
		} else if ch >= '\u03F0' && ch <= '\u03F5' {
			return true
		} else if ch == '\u0190' || ch == '\u025B' {
			return true
		}
	}

	return false
}

func HasHyphenOrApostrophe(str string) bool {

	for _, ch := range str {
		if ch == '-' || ch == '\'' {
			return true
		}
	}

	return false
}

func HasPlusOrMinus(str string) bool {

	for _, ch := range str {
		if ch == '-' || ch == '+' {
			return true
		}
	}

	return false
}

func HasSpaceOrHyphen(str string) bool {

	for _, ch := range str {
		if ch == ' ' || ch == '-' {
			return true
		}
	}

	return false
}

func HasUnicodeMarkup(str string) bool {

	for _, ch := range str {
		if ch <= 127 {
			continue
		}
		// check for Unicode superscript or subscript characters
		if ch == '\u00B2' || ch == '\u00B3' || ch == '\u00B9' || (ch >= '\u2070' && ch <= '\u208E') {
			return true
		}
	}

	return false
}

func HTMLAhead(text string, idx, txtlen int) int {

	// record position of < character
	start := idx

	// at start of element
	idx++
	if idx >= txtlen {
		return 0
	}
	ch := text[idx]

	if ch == '/' {
		// skip past end tag symbol
		idx++
		ch = text[idx]
	}

	// all embedded markup tags start with a lower-case letter
	if ch < 'a' || ch > 'z' {
		// except for DispFormula in PubmedArticle
		if ch == 'D' && strings.HasPrefix(text[idx:], "DispFormula") {
			for ch != '>' {
				idx++
				ch = text[idx]
			}
			return idx + 1 - start
		}

		// otherwise not a recognized markup tag
		return 0
	}

	idx++
	ch = text[idx]
	for InLower[ch] {
		idx++
		ch = text[idx]
	}

	// if tag name was not all lower-case, then exit
	if ch >= 'A' && ch <= 'Z' {
		return 0
	}

	// skip to end of element, past any attributes or slash character
	for ch != '>' {
		idx++
		ch = text[idx]
	}

	// return number of characters to advance to skip this markup tag
	return idx + 1 - start
}

func HTMLBehind(bufr []byte, pos, txtlen int) bool {

	for pos >= 0 {
		if bufr[pos] == '<' {
			return HTMLAhead(string(bufr), pos, txtlen) != 0
		}
		pos--
	}

	return false
}

func IsAllCapsOrDigits(str string) bool {

	for _, ch := range str {
		if !unicode.IsUpper(ch) && !unicode.IsDigit(ch) {
			return false
		}
	}

	return true
}

func IsAllDigits(str string) bool {

	for _, ch := range str {
		if !unicode.IsDigit(ch) {
			return false
		}
	}

	return true
}

func IsAllDigitsOrPeriod(str string) bool {

	for _, ch := range str {
		if !unicode.IsDigit(ch) && ch != '.' {
			return false
		}
	}

	return true
}

func IsAllNumeric(str string) bool {

	for _, ch := range str {
		if !unicode.IsDigit(ch) &&
			ch != '.' &&
			ch != '+' &&
			ch != '-' &&
			ch != '*' &&
			ch != '/' &&
			ch != ',' &&
			ch != '$' &&
			ch != '#' &&
			ch != '%' &&
			ch != '(' &&
			ch != ')' {
			return false
		}
	}

	return true
}

func IsNotASCII(str string) bool {

	for _, ch := range str {
		if ch > 127 {
			return true
		}
	}

	return false
}

func IsNotJustWhitespace(str string) bool {

	for _, ch := range str {
		if ch > 127 || !InBlank[ch] {
			return true
		}
	}

	return false
}

var plock sync.RWMutex

func IsStopWord(str string) bool {

	plock.RLock()
	isSW := isStopWord[str]
	plock.RUnlock()

	return isSW
}

func IsUnicodeSubsc(ch rune) bool {
	return ch >= '\u2080' && ch <= '\u208E'
}

func IsUnicodeSuper(ch rune) bool {
	return ch == '\u00B2' || ch == '\u00B3' || ch == '\u00B9' || (ch >= '\u2070' && ch <= '\u207F')
}

func NeedsTightening(str string) bool {

	if len(str) < 2 {
		return false
	}

	var prev rune

	for _, ch := range str {
		if prev == '(' && ch == ' ' {
			return true
		}
		if prev == ' ' && ch == ')' {
			return true
		}
		prev = ch
	}

	return false
}

func ParseIndex(indx string) *Find {

	if indx == "" {
		return &Find{}
	}

	// parse parent/element@attribute^version index
	prnt, match := SplitInTwoAt(indx, "/", RIGHT)
	match, versn := SplitInTwoAt(match, "^", LEFT)
	match, attrib := SplitInTwoAt(match, "@", LEFT)

	return &Find{Index: indx, Parent: prnt, Match: match, Attrib: attrib, Versn: versn}
}

func RemoveCommaOrSemicolon(str string) string {

	str = strings.ToLower(str)

	if HasCommaOrSemicolon(str) {
		str = strings.Replace(str, ",", " ", -1)
		str = strings.Replace(str, ";", " ", -1)
		str = CompressRunsOfSpaces(str)
	}
	str = strings.TrimSpace(str)
	str = strings.TrimRight(str, ".?:")

	return str
}

func RemoveEmbeddedMarkup(str string) string {

	inContent := true
	var buffer strings.Builder

	for _, ch := range str {
		if ch == '<' {
			inContent = false
		} else if ch == '>' {
			inContent = true
		} else if inContent {
			buffer.WriteRune(ch)
		}
	}

	return buffer.String()
}

func RepairEncodedMarkup(str string) string {

	var buffer strings.Builder

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

	skip := 0

	for i, ch := range str {
		if skip > 0 {
			skip--
			continue
		}
		if ch == '<' {
			// remove internal tags in runs of subscripts or superscripts
			if strings.HasPrefix(str[i:], "</sub><sub>") || strings.HasPrefix(str[i:], "</sup><sup>") {
				skip = 10
				continue
			}
			buffer.WriteRune(ch)
			continue
		} else if ch != '&' {
			buffer.WriteRune(ch)
			continue
		} else if strings.HasPrefix(str[i:], "&lt;") {
			sub := lookAhead(str[i:], 14)
			txt, ok := htmlRepair[sub]
			if ok {
				adv := len(sub) - 1
				// do not convert if flanked by spaces - it may be a scientific symbol,
				// e.g., fragments <i> in PMID 9698410, or escaped <b> and <d> tags used
				// to indicate stem position in letters in PMID 21892341
				if i < 1 || str[i-1] != ' ' || !strings.HasPrefix(str[i+adv:], "; ") {
					buffer.WriteString(txt)
					skip = adv
					continue
				}
			}
		} else if strings.HasPrefix(str[i:], "&amp;") {
			if strings.HasPrefix(str[i:], "&amp;lt;") {
				sub := lookAhead(str[i:], 22)
				txt, ok := htmlRepair[sub]
				if ok {
					buffer.WriteString(txt)
					skip = len(sub) - 1
					continue
				} else {
					buffer.WriteString("&lt;")
					skip = 7
					continue
				}
			} else if strings.HasPrefix(str[i:], "&amp;gt;") {
				buffer.WriteString("&gt;")
				skip = 7
				continue
			} else {
				skip = 4
				j := i + 5
				// remove runs of multiply-encoded ampersands
				for strings.HasPrefix(str[j:], "amp;") {
					skip += 4
					j += 4
				}
				// then look for special symbols used in PubMed records
				if strings.HasPrefix(str[j:], "lt;") {
					buffer.WriteString("&lt;")
					skip += 3
				} else if strings.HasPrefix(str[j:], "gt;") {
					buffer.WriteString("&gt;")
					skip += 3
				} else if strings.HasPrefix(str[j:], "frac") {
					buffer.WriteString("&frac")
					skip += 4
				} else if strings.HasPrefix(str[j:], "plusmn") {
					buffer.WriteString("&plusmn")
					skip += 6
				} else if strings.HasPrefix(str[j:], "acute") {
					buffer.WriteString("&acute")
					skip += 5
				} else if strings.HasPrefix(str[j:], "aacute") {
					buffer.WriteString("&aacute")
					skip += 6
				} else if strings.HasPrefix(str[j:], "rsquo") {
					buffer.WriteString("&rsquo")
					skip += 5
				} else if strings.HasPrefix(str[j:], "lsquo") {
					buffer.WriteString("&lsquo")
					skip += 5
				} else if strings.HasPrefix(str[j:], "micro") {
					buffer.WriteString("&micro")
					skip += 5
				} else if strings.HasPrefix(str[j:], "oslash") {
					buffer.WriteString("&oslash")
					skip += 6
				} else if strings.HasPrefix(str[j:], "kgr") {
					buffer.WriteString("&kgr")
					skip += 3
				} else if strings.HasPrefix(str[j:], "apos") {
					buffer.WriteString("&apos")
					skip += 4
				} else if strings.HasPrefix(str[j:], "quot") {
					buffer.WriteString("&quot")
					skip += 4
				} else if strings.HasPrefix(str[j:], "alpha") {
					buffer.WriteString("&alpha")
					skip += 5
				} else if strings.HasPrefix(str[j:], "beta") {
					buffer.WriteString("&beta")
					skip += 4
				} else if strings.HasPrefix(str[j:], "gamma") {
					buffer.WriteString("&gamma")
					skip += 5
				} else if strings.HasPrefix(str[j:], "Delta") {
					buffer.WriteString("&Delta")
					skip += 5
				} else if strings.HasPrefix(str[j:], "phi") {
					buffer.WriteString("&phi")
					skip += 3
				} else if strings.HasPrefix(str[j:], "ge") {
					buffer.WriteString("&ge")
					skip += 2
				} else if strings.HasPrefix(str[j:], "sup2") {
					buffer.WriteString("&sup2")
					skip += 4
				} else if strings.HasPrefix(str[j:], "#") {
					buffer.WriteString("&")
				} else {
					buffer.WriteString("&amp;")
				}
				continue
			}
		}

		// if loop not continued by any preceding test, print character
		buffer.WriteRune(ch)
	}

	return buffer.String()
}

func RepairMathMLMarkup(str string, policy MarkupPolicy) string {

	str = strings.Replace(str, "> <mml:", "><mml:", -1)
	str = strings.Replace(str, "> </mml:", "></mml:", -1)

	findNextMathBlock := func(txt string) (int, int, bool) {

		beg := strings.Index(txt, "<DispFormula")
		if beg < 0 {
			return -1, -1, false
		}
		end := strings.Index(txt, "</DispFormula>")
		if end < 0 {
			return -1, -1, false
		}
		end += 14
		return beg, end, true
	}

	var arry []string

	for {
		beg, end, ok := findNextMathBlock(str)
		if !ok {
			break
		}
		pfx := str[:beg]
		pfx = strings.TrimSpace(pfx)
		arry = append(arry, pfx)
		tmp := str[beg:end]
		if strings.HasPrefix(tmp, "<DispFormula") {
			tmp = FlattenMathML(tmp, policy)
		}
		tmp = strings.TrimSpace(tmp)
		arry = append(arry, tmp)
		str = str[end:]
	}

	str = strings.TrimSpace(str)
	arry = append(arry, str)

	return strings.Join(arry, " ")
}

func RepairScriptMarkup(str string, policy MarkupPolicy) string {

	var buffer strings.Builder

	skip := 0

	for i, ch := range str {
		if skip > 0 {
			skip--
			continue
		}
		if ch == '<' {
			if strings.HasPrefix(str[i:], "<sub>") {
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
					buffer.WriteRune('(')
				case MARKDOWN:
					buffer.WriteRune('~')
				}
				skip = 4
				continue
			}
			if strings.HasPrefix(str[i:], "<sup>") {
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
					buffer.WriteRune('[')
				case MARKDOWN:
					buffer.WriteRune('^')
				}
				skip = 4
				continue
			}
			if strings.HasPrefix(str[i:], "</sub>") {
				if strings.HasPrefix(str[i+6:], "<sup>") {
					switch policy {
					case PERIOD:
						buffer.WriteRune('.')
					case SPACE:
						buffer.WriteRune(' ')
					case BRACKETS:
						buffer.WriteRune(')')
						buffer.WriteRune('[')
					case MARKDOWN:
						buffer.WriteRune('~')
						buffer.WriteRune('^')
					}
					skip = 10
					continue
				}
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
					buffer.WriteRune(')')
				case MARKDOWN:
					buffer.WriteRune('~')
				}
				skip = 5
				continue
			}
			if strings.HasPrefix(str[i:], "</sup>") {
				if strings.HasPrefix(str[i+6:], "<sub>") {
					switch policy {
					case PERIOD:
						buffer.WriteRune('.')
					case SPACE:
						buffer.WriteRune(' ')
					case BRACKETS:
						buffer.WriteRune(']')
						buffer.WriteRune('(')
					case MARKDOWN:
						buffer.WriteRune('^')
						buffer.WriteRune('~')
					}
					skip = 10
					continue
				}
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
					buffer.WriteRune(']')
				case MARKDOWN:
					buffer.WriteRune('^')
				}
				skip = 5
				continue
			}
		}

		buffer.WriteRune(ch)
	}

	return buffer.String()
}

func RepairTableMarkup(str string, policy MarkupPolicy) string {

	str = strings.Replace(str, "<tr>", " ", -1)
	str = strings.Replace(str, "<td>", " ", -1)
	str = strings.Replace(str, "</tr>", " ", -1)
	str = strings.Replace(str, "</td>", " ", -1)

	return str
}

func RepairUnicodeMarkup(str string, policy MarkupPolicy) string {

	type MarkupType int

	const (
		NOSCRIPT MarkupType = iota
		SUPSCRIPT
		SUBSCRIPT
		PLAINDIGIT
	)

	var buffer strings.Builder

	// to improve readability, keep track of switches between numeric types, add period at transitions when converting to plain ASCII
	level := NOSCRIPT

	for _, ch := range str {
		if ch > 127 {
			if IsUnicodeSuper(ch) {
				rn, ok := scriptRunes[ch]
				if ok {
					ch = rn
					switch level {
					case NOSCRIPT:
						switch policy {
						case PERIOD:
						case SPACE:
						case BRACKETS:
							buffer.WriteRune('[')
						case MARKDOWN:
							buffer.WriteRune('^')
						case SLASH:
						case TAGS:
							buffer.WriteString("<sup>")
						}
					case SUPSCRIPT:
						switch policy {
						case PERIOD:
						case SPACE:
						case BRACKETS:
						case MARKDOWN:
						case SLASH:
						case TAGS:
						}
					case SUBSCRIPT:
						switch policy {
						case PERIOD:
							buffer.WriteRune('.')
						case SPACE:
							buffer.WriteRune(' ')
						case BRACKETS:
							buffer.WriteRune(')')
							buffer.WriteRune('[')
						case MARKDOWN:
							buffer.WriteRune('~')
							buffer.WriteRune('^')
						case SLASH:
							buffer.WriteRune('\\')
						case TAGS:
							buffer.WriteString("</sub>")
							buffer.WriteString("<sup>")
						}
					case PLAINDIGIT:
						switch policy {
						case PERIOD:
							buffer.WriteRune('.')
						case SPACE:
							buffer.WriteRune(' ')
						case BRACKETS:
							buffer.WriteRune('[')
						case MARKDOWN:
							buffer.WriteRune('^')
						case SLASH:
							buffer.WriteRune('\\')
						case TAGS:
							buffer.WriteString("<sup>")
						}
					}
					level = SUPSCRIPT
				}
			} else if IsUnicodeSubsc(ch) {
				rn, ok := scriptRunes[ch]
				if ok {
					ch = rn
					switch level {
					case NOSCRIPT:
						switch policy {
						case PERIOD:
						case SPACE:
						case BRACKETS:
							buffer.WriteRune('(')
						case MARKDOWN:
							buffer.WriteRune('~')
						case SLASH:
						case TAGS:
							buffer.WriteString("<sub>")
						}
					case SUPSCRIPT:
						switch policy {
						case PERIOD:
							buffer.WriteRune('.')
						case SPACE:
							buffer.WriteRune(' ')
						case BRACKETS:
							buffer.WriteRune(']')
							buffer.WriteRune('(')
						case MARKDOWN:
							buffer.WriteRune('^')
							buffer.WriteRune('~')
						case SLASH:
							buffer.WriteRune('/')
						case TAGS:
							buffer.WriteString("</sup>")
							buffer.WriteString("<sub>")
						}
					case SUBSCRIPT:
						switch policy {
						case PERIOD:
						case SPACE:
						case BRACKETS:
						case MARKDOWN:
						case SLASH:
						case TAGS:
						}
					case PLAINDIGIT:
						switch policy {
						case PERIOD:
							buffer.WriteRune('.')
						case SPACE:
							buffer.WriteRune(' ')
						case BRACKETS:
							buffer.WriteRune('(')
						case MARKDOWN:
							buffer.WriteRune('~')
						case SLASH:
							buffer.WriteRune('/')
						case TAGS:
							buffer.WriteString("<sub>")
						}
					}
					level = SUBSCRIPT
				}
			} else {
				level = NOSCRIPT
			}
		} else if ch >= '0' && ch <= '9' {
			switch level {
			case NOSCRIPT:
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
				case MARKDOWN:
				case SLASH:
				case TAGS:
				}
			case SUPSCRIPT:
				switch policy {
				case PERIOD:
					buffer.WriteRune('.')
				case SPACE:
					buffer.WriteRune(' ')
				case BRACKETS:
					buffer.WriteRune(']')
				case MARKDOWN:
					buffer.WriteRune('^')
				case SLASH:
					buffer.WriteRune('/')
				case TAGS:
					buffer.WriteString("</sup>")
				}
			case SUBSCRIPT:
				switch policy {
				case PERIOD:
					buffer.WriteRune('.')
				case SPACE:
					buffer.WriteRune(' ')
				case BRACKETS:
					buffer.WriteRune(')')
				case MARKDOWN:
					buffer.WriteRune('~')
				case SLASH:
					buffer.WriteRune('\\')
				case TAGS:
					buffer.WriteString("</sub>")
				}
			case PLAINDIGIT:
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
				case MARKDOWN:
				case SLASH:
				case TAGS:
				}
			}
			level = PLAINDIGIT
		} else {
			switch level {
			case NOSCRIPT:
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
				case MARKDOWN:
				case SLASH:
				case TAGS:
				}
			case SUPSCRIPT:
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
					buffer.WriteRune(']')
				case MARKDOWN:
					buffer.WriteRune('^')
				case SLASH:
				case TAGS:
					buffer.WriteString("</sup>")
				}
			case SUBSCRIPT:
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
					buffer.WriteRune(')')
				case MARKDOWN:
					buffer.WriteRune('~')
				case SLASH:
				case TAGS:
					buffer.WriteString("</sub>")
				}
			case PLAINDIGIT:
				switch policy {
				case PERIOD:
				case SPACE:
				case BRACKETS:
				case MARKDOWN:
				case SLASH:
				case TAGS:
				}
			}
			level = NOSCRIPT
		}
		buffer.WriteRune(ch)
	}

	switch level {
	case NOSCRIPT:
		switch policy {
		case PERIOD:
		case SPACE:
		case BRACKETS:
		case MARKDOWN:
		case SLASH:
		case TAGS:
		}
	case SUPSCRIPT:
		switch policy {
		case PERIOD:
		case SPACE:
		case BRACKETS:
			buffer.WriteRune(']')
		case MARKDOWN:
			buffer.WriteRune('^')
		case SLASH:
		case TAGS:
			buffer.WriteString("</sup>")
		}
	case SUBSCRIPT:
		switch policy {
		case PERIOD:
		case SPACE:
		case BRACKETS:
			buffer.WriteRune(')')
		case MARKDOWN:
			buffer.WriteRune('~')
		case SLASH:
		case TAGS:
			buffer.WriteString("</sub>")
		}
	case PLAINDIGIT:
		switch policy {
		case PERIOD:
		case SPACE:
		case BRACKETS:
		case MARKDOWN:
		case SLASH:
		case TAGS:
		}
	}

	return buffer.String()
}

func SortStringByWords(str string) string {

	str = RemoveCommaOrSemicolon(str)

	if HasSpaceOrHyphen(str) {
		flds := strings.Fields(str)
		sort.Slice(flds, func(i, j int) bool { return flds[i] < flds[j] })
		str = strings.Join(flds, " ")
		str = strings.Replace(str, "-", " ", -1)
		str = CompressRunsOfSpaces(str)
		str = strings.TrimRight(str, ".?:")
	}

	return str
}

func SpellGreek(str string) string {

	var buffer strings.Builder

	for _, ch := range str {
		st := ""
		ok := false
		if ch > 127 {
			if (ch >= '\u03B1' && ch <= '\u03C9') || (ch >= '\u0391' && ch <= '\u03A9') {
				st, ok = greekRunes[ch]
			} else if (ch >= '\u03D1' && ch <= '\u03D6') || (ch >= '\u03F0' && ch <= '\u03F5') {
				// glyph variants of Greek letters
				st, ok = greekRunes[ch]
			} else if ch == '\u0190' || ch == '\u025B' {
				// treat latin letter open E as epsilon
				st, ok = greekRunes[ch]
			}
		}
		if ok {
			buffer.WriteString(" ")
			buffer.WriteString(st)
			buffer.WriteString(" ")
			continue
		}
		buffer.WriteRune(ch)
	}

	return buffer.String()
}

func SplitInTwoAt(str, chr string, side SideType) (string, string) {

	slash := strings.SplitN(str, chr, 2)
	if len(slash) > 1 {
		return slash[0], slash[1]
	}

	if side == LEFT {
		return str, ""
	}

	return "", str
}

func TightenParentheses(str string) string {

	if len(str) < 2 {
		return str
	}

	var (
		buffer strings.Builder
		prev   rune
	)

	for _, ch := range str {
		if prev == '(' && ch == ' ' {
			ch = '('
		} else if prev == ' ' && ch == ')' {
			ch = ')'
		} else if prev != 0 {
			buffer.WriteRune(prev)
		}
		prev = ch
	}

	buffer.WriteRune(prev)

	return buffer.String()
}

func UnicodeToASCII(str string) string {

	var buffer strings.Builder

	for _, ch := range str {
		if ch > 127 {
			s := strconv.QuoteToASCII(string(ch))
			s = strings.ToUpper(s[3:7])
			for {
				if !strings.HasPrefix(s, "0") {
					break
				}
				s = s[1:]
			}
			buffer.WriteString("&#x")
			buffer.WriteString(s)
			buffer.WriteRune(';')
			continue
		}
		buffer.WriteRune(ch)
	}

	return buffer.String()
}

// READ XML INPUT FILE INTO CHANNEL OF TRIMMED BLOCKS

func CreateReader(in io.Reader) <-chan string {

	if in == nil {
		return nil
	}

	out := make(chan string, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create block reader channel\n")
		os.Exit(1)
	}

	// xmlReader sends XML blocks through channel
	xmlReader := func(in io.Reader, out chan<- string) {

		// close channel when all blocks have been processed
		defer close(out)

		// 65536 appears to be the maximum number of characters presented to io.Reader when input is piped from stdin
		// increasing size of buffer when input is from a file does not improve program performance
		// additional 16384 bytes are reserved for copying previous remainder to start of buffer before next read
		const XMLBUFSIZE = 65536 + 16384

		Buffer := make([]byte, XMLBUFSIZE)
		Remainder := ""
		Position := int64(0)
		Delta := 0
		Closed := false

		// read one buffer, trim at last > and retain remainder for next call, signal if no > character
		nextBuffer := func() ([]byte, bool, bool) {

			if Closed {
				return nil, false, true
			}

			// prepend previous remainder to beginning of buffer
			m := copy(Buffer, Remainder)
			Remainder = ""
			if m > 16384 {
				// previous remainder is larger than reserved section, write and signal need to continue reading
				return Buffer[:m], true, false
			}

			// read next block, append behind copied remainder from previous read
			n, err := in.Read(Buffer[m:])
			// with data piped through stdin, read function may not always return the same number of bytes each time
			if err != nil {
				if err != io.EOF {
					// real error
					fmt.Fprintf(os.Stderr, "\nERROR: %s\n", err.Error())
					// Ignore bytes - non-conforming implementations of io.Reader may returned mangled data on non-EOF errors
					Closed = true
					return nil, false, true
				}
				// end of file
				Closed = true
				if n == 0 {
					// if EOF and no more data, do not send final remainder (not terminated by right angle bracket that is used as a sentinel)
					return nil, false, true
				}
			}
			if n < 0 {
				// Reality check - non-conforming implementations of io.Reader may return -1
				fmt.Fprintf(os.Stderr, "\nERROR: io.Reader returned negative count %d\n", n)
				// treat as n == 0 in order to update file offset and avoid losing previous remainder
				n = 0
			}

			// keep track of file offset
			Position += int64(Delta)
			Delta = n

			// slice of actual characters read
			bufr := Buffer[:n+m]

			// look for last > character
			// safe to back up on UTF-8 rune array when looking for 7-bit ASCII character
			pos := -1
			for pos = len(bufr) - 1; pos >= 0; pos-- {
				if bufr[pos] == '>' {
					if DoStrict {
						// optionally skip backwards past embedded i, b, u, sub, and sup HTML open, close, and empty tags, and MathML
						if HTMLBehind(bufr, pos, len(bufr)) {
							continue
						}
					}
					// found end of XML tag, break
					break
				}
			}

			// trim back to last > character, save remainder for next buffer
			if pos > -1 {
				pos++
				Remainder = string(bufr[pos:])
				return bufr[:pos], false, false
			}

			// no > found, signal need to continue reading long content
			return bufr[:], true, false
		}

		// nextBlock reads buffer, concatenates if necessary to place long element content into a single string
		// all result strings end in > character that is used as a sentinel in subsequent code
		nextBlock := func() string {

			// read next buffer
			line, cont, closed := nextBuffer()

			if closed {
				// no sentinel in remainder at end of file
				return ""
			}

			// if buffer does not end with > character
			if cont {
				var buff bytes.Buffer

				// keep reading long content blocks
				for {
					if len(line) > 0 {
						buff.Write(line)
					}
					if !cont {
						// last buffer ended with sentinel
						break
					}
					line, cont, closed = nextBuffer()
					if closed {
						// no sentinel in multi-block buffer at end of file
						return ""
					}
				}

				// concatenate blocks
				return buff.String()
			}

			return string(line)
		}

		// read XML and send blocks through channel
		for {
			str := nextBlock()

			// trimming spaces here would throw off line tracking

			// optionally compress/cleanup tags/attributes and contents (undocumented)
			if DoCleanup {
				if HasBadSpace(str) {
					str = CleanupBadSpaces(str)
				}
				if HasAdjacentSpaces(str) {
					str = CompressRunsOfSpaces(str)
				}
			}

			out <- str

			// bail after sending empty string sentinel
			if str == "" {
				return
			}
		}
	}

	// launch single block reader goroutine
	go xmlReader(in, out)

	return out
}

// PARSE XML BLOCK STREAM INTO STRINGS FROM <PATTERN> TO </PATTERN>

// PartitionPattern splits XML input by pattern and sends individual records to a callback
func PartitionPattern(pat, star string, inp <-chan string, proc func(string)) {

	if pat == "" || inp == nil || proc == nil {
		return
	}

	type Scanner struct {
		Pattern   string
		PatLength int
		CharSkip  [256]int
	}

	// initialize <pattern> to </pattern> scanner
	newScanner := func(pattern string) *Scanner {

		if pattern == "" {
			return nil
		}

		scr := &Scanner{Pattern: pattern}

		patlen := len(pattern)
		scr.PatLength = patlen

		// position of last character in pattern
		last := patlen - 1

		// initialize bad character displacement table
		for i := range scr.CharSkip {
			scr.CharSkip[i] = patlen
		}
		for i := 0; i < last; i++ {
			ch := pattern[i]
			scr.CharSkip[ch] = last - i
		}

		return scr
	}

	// check surroundings of match candidate
	isAnElement := func(text string, lf, rt, mx int) bool {

		if (lf >= 0 && text[lf] == '<') || (lf > 0 && text[lf] == '/' && text[lf-1] == '<') {
			if (rt < mx && (text[rt] == '>' || text[rt] == ' ' || text[rt] == '\n')) || (rt+1 < mx && text[rt] == '/' && text[rt+1] == '>') {
				return true
			}
		}

		return false
	}

	// modified Boyer-Moore-Horspool search function
	findNextMatch := func(scr *Scanner, text string, offset int) (int, int, int) {

		if scr == nil || text == "" {
			return -1, -1, -1
		}

		// copy values into local variables for speed
		txtlen := len(text)
		pattern := scr.Pattern[:]
		patlen := scr.PatLength
		max := txtlen - patlen
		last := patlen - 1
		skip := scr.CharSkip[:]

		i := offset

		for i <= max {
			j := last
			k := i + last
			for j >= 0 && text[k] == pattern[j] {
				j--
				k--
			}
			// require match candidate to be element name, i.e., <pattern ... >, </pattern ... >, or <pattern ... />
			if j < 0 && isAnElement(text, i-1, i+patlen, txtlen) {
				// find positions of flanking brackets
				lf := i - 1
				for lf > 0 && text[lf] != '<' {
					lf--
				}
				rt := i + patlen
				for rt < txtlen && text[rt] != '>' {
					rt++
				}
				return i + 1, lf, rt + 1
			}
			// find character in text above last character in pattern
			ch := text[i+last]
			// displacement table can shift pattern by one or more positions
			i += skip[ch]
		}

		return -1, -1, -1
	}

	type PatternType int

	const (
		NOPATTERN PatternType = iota
		STARTPATTERN
		SELFPATTERN
		STOPPATTERN
	)

	// find next element with pattern name
	nextPattern := func(scr *Scanner, text string, pos int) (PatternType, int, int, int) {

		if scr == nil || text == "" {
			return NOPATTERN, 0, 0, 0
		}

		prev := pos

		for {
			next, start, stop := findNextMatch(scr, text, prev)
			if next < 0 {
				return NOPATTERN, 0, 0, 0
			}

			prev = next + 1

			if text[start+1] == '/' {
				return STOPPATTERN, start, stop, prev
			} else if text[stop-2] == '/' {
				return SELFPATTERN, start, stop, prev
			} else {
				return STARTPATTERN, start, stop, prev
			}
		}
	}

	// -pattern Object construct

	doNormal := func() {

		// current depth of -pattern objects
		level := 0

		begin := 0
		inPattern := false

		line := ""
		var accumulator strings.Builder

		match := NOPATTERN
		start := 0
		stop := 0
		next := 0

		scr := newScanner(pat)
		if scr == nil {
			return
		}

		for {

			begin = 0
			next = 0

			line = <-inp
			if line == "" {
				return
			}

			for {
				match, start, stop, next = nextPattern(scr, line, next)
				if match == STARTPATTERN {
					if level == 0 {
						inPattern = true
						begin = start
					}
					level++
				} else if match == STOPPATTERN {
					level--
					if level == 0 {
						inPattern = false
						accumulator.WriteString(line[begin:stop])
						// read and process one -pattern object at a time
						str := accumulator.String()
						if str != "" {
							proc(str[:])
						}
						// reset accumulator
						accumulator.Reset()
					}
				} else if match == SELFPATTERN {
					if level == 0 {
						str := line[start:stop]
						if str != "" {
							proc(str[:])
						}
					}
				} else {
					if inPattern {
						accumulator.WriteString(line[begin:])
					}
					break
				}
			}
		}
	}

	// -pattern Parent/* construct now works with catenated files, but not if components
	// are recursive or self-closing objects, process those through -format first

	doStar := func() {

		// current depth of -pattern objects
		level := 0

		begin := 0
		inPattern := false

		line := ""
		var accumulator strings.Builder

		match := NOPATTERN
		start := 0
		stop := 0
		next := 0

		scr := newScanner(pat)
		if scr == nil {
			return
		}

		last := pat

		// read to first <pattern> element
		for {

			next = 0

			line = <-inp
			if line == "" {
				break
			}

			match, start, stop, next = nextPattern(scr, line, next)
			if match == STARTPATTERN {
				break
			}
		}

		if match != STARTPATTERN {
			return
		}

		// find next element in XML
		nextElement := func(text string, pos int) string {

			txtlen := len(text)

			tag := ""
			for i := pos; i < txtlen; i++ {
				if text[i] == '<' {
					tag = text[i+1:]
					break
				}
			}
			if tag == "" {
				return ""
			}
			if tag[0] == '/' {
				if strings.HasPrefix(tag[1:], pat) {
					//should be </pattern> at end, want to continue if catenated files
					return "/"
				}
				return ""
			}
			for i, ch := range tag {
				if ch == '>' || ch == ' ' || ch == '/' {
					return tag[0:i]
				}
			}

			return ""
		}

		// read and process heterogeneous objects immediately below <pattern> parent
		for {
			tag := nextElement(line, next)
			if tag == "" {

				begin = 0
				next = 0

				line = <-inp
				if line == "" {
					break
				}

				tag = nextElement(line, next)
			}
			if tag == "" {
				return
			}

			// check for catenated parent set files
			if tag[0] == '/' {
				scr = newScanner(pat)
				if scr == nil {
					return
				}
				last = pat
				// confirm end </pattern> just found
				match, start, stop, next = nextPattern(scr, line, next)
				if match != STOPPATTERN {
					return
				}
				// now look for a new start <pattern> tag
				for {
					match, start, stop, next = nextPattern(scr, line, next)
					if match == STARTPATTERN {
						break
					}
					next = 0
					line = <-inp
					if line == "" {
						break
					}
				}
				if match != STARTPATTERN {
					return
				}
				// continue with processing loop
				continue
			}

			if tag != last {
				scr = newScanner(tag)
				if scr == nil {
					return
				}
				last = tag
			}

			for {
				match, start, stop, next = nextPattern(scr, line, next)
				if match == STARTPATTERN {
					if level == 0 {
						inPattern = true
						begin = start
					}
					level++
				} else if match == STOPPATTERN {
					level--
					if level == 0 {
						inPattern = false
						accumulator.WriteString(line[begin:stop])
						// read and process one -pattern/* object at a time
						str := accumulator.String()
						if str != "" {
							proc(str[:])
						}
						// reset accumulator
						accumulator.Reset()
						break
					}
				} else if match == SELFPATTERN {
					if level == 0 {
						str := line[start:stop]
						if str != "" {
							proc(str[:])
						}
					}
				} else {
					if inPattern {
						accumulator.WriteString(line[begin:])
					}

					begin = 0
					next = 0

					line = <-inp
					if line == "" {
						break
					}
				}
			}
		}
	}

	// call appropriate handler
	if star == "" {
		doNormal()
	} else if star == "*" {
		doStar()
	}
}

// PARSE ATTRIBUTES INTO TAG/VALUE PAIRS

// ParseAttributes is only run if attribute values are requested in element statements
func ParseAttributes(attrb string) []string {

	if attrb == "" {
		return nil
	}

	attlen := len(attrb)

	// count equal signs
	num := 0
	inQuote := false

	for i := 0; i < attlen; i++ {
		ch := attrb[i]
		if ch == '"' || ch == '\'' {
			// "
			inQuote = !inQuote
		}
		if ch == '=' && !inQuote {
			num += 2
		}
	}
	if num < 1 {
		return nil
	}

	// allocate array of proper size
	arry := make([]string, num)
	if arry == nil {
		return nil
	}

	start := 0
	idx := 0
	itm := 0
	inQuote = false

	// place tag and value in successive array slots
	for idx < attlen && itm < num {
		ch := attrb[idx]
		if ch == '"' || ch == '\'' {
			// "
			inQuote = !inQuote
		}
		if ch == '=' && !inQuote {
			inQuote = true
			// skip past possible leading blanks
			for start < attlen {
				ch = attrb[start]
				if InBlank[ch] {
					start++
				} else {
					break
				}
			}
			// =
			arry[itm] = strings.TrimSpace(attrb[start:idx])
			itm++
			// skip past equal sign
			idx++
			ch = attrb[idx]
			if ch != '"' && ch != '\'' {
				// "
				// skip past unexpected blanks
				for InBlank[ch] {
					idx++
					ch = attrb[idx]
				}
				if ch != '"' && ch != '\'' {
					// "
					fmt.Fprintf(os.Stderr, "\nAttribute in '%s' missing double quote\n", attrb)
				}
			}
			// skip past leading double quote
			idx++
			start = idx
		} else if ch == '"' || ch == '\'' {
			// "
			inQuote = false
			arry[itm] = strings.TrimSpace(attrb[start:idx])
			itm++
			// skip past trailing double quote and (possible) space
			idx += 2
			start = idx
		} else {
			idx++
		}
	}

	return arry
}

// ParseXML calls XML parser on a partitioned string, optimized for maximum processing speed,
// or on an XML reader, sending tokens for CDATA and COMMENT sections, and optionally tracks line numbers
func ParseXML(Text, parent string, inp <-chan string, tokens func(Token), find *Find, ids func(string)) (*Node, string) {

	if Text == "" && (inp == nil || tokens == nil) {
		return nil, ""
	}

	// token parser variables
	Txtlen := len(Text)
	Idx := 0

	// line tracking variables
	Line := 1
	Lag := 0

	// variables to track COMMENT or CDATA sections that span reader blocks
	Which := NOTAG
	SkipTo := ""

	updateLineCount := func(max int) {
		// count lines
		for i := Lag; i < max; i++ {
			if Text[i] == '\n' {
				Line++
			}
		}
		Lag = Idx
	}

	// calculate for warning messages, do not update Line or Lag variables
	currentLineCount := func(max int) int {
		line := Line
		for i := Lag; i < max; i++ {
			if Text[i] == '\n' {
				line++
			}
		}
		return line
	}

	// get next XML token
	nextToken := func(idx int) (TagType, ContentType, string, string, int) {

		if Text == "" {
			// buffer is empty
			if inp != nil {
				// read next block if available
				Text = <-inp
				Txtlen = len(Text)
				Idx = 0
				idx = 0
				Lag = 0
			}

			if Text == "" {
				// signal end of XML data
				return ISCLOSED, NONE, "", "", 0
			}

			if Which != NOTAG && SkipTo != "" {
				// previous block ended inside CDATA object or COMMENT
				text := Text[:]
				txtlen := Txtlen
				which := Which
				start := idx
				found := strings.Index(text[idx:], SkipTo)
				if found < 0 {
					// no stop signal found in next block
					str := text[start:]
					if HasFlankingSpace(str) {
						str = strings.TrimSpace(str)
					}

					if CountLines {
						updateLineCount(txtlen)
					}

					// signal end of current block
					Text = ""

					// leave Which and SkipTo values unchanged as another continuation signal
					// send CDATA or COMMENT contents
					return which, NONE, str[:], "", 0
				}
				// otherwise adjust position past end of skipTo string and return to normal processing
				idx += found
				str := text[start:idx]
				if HasFlankingSpace(str) {
					str = strings.TrimSpace(str)
				}
				idx += len(SkipTo)
				// clear tracking variables
				Which = NOTAG
				SkipTo = ""
				// send CDATA or COMMENT contents
				return which, NONE, str[:], "", idx
			}
		}

		text := Text[:]
		txtlen := Txtlen

		// XML string, and all blocks, end with > character, acts as sentinel to check if past end of text
		if idx >= txtlen {
			if inp != nil {

				if CountLines {
					updateLineCount(txtlen)
				}

				// signal end of current block, will read next block on next call
				Text = ""

				return NOTAG, NONE, "", "", 0
			}

			// signal end of XML string
			return ISCLOSED, NONE, "", "", 0
		}

		ctype := NONE

		// skip past leading blanks
		ch := text[idx]
		if InBlank[ch] {
			ctype |= LFTSPACE
			idx++
			ch = text[idx]
			for InBlank[ch] {
				idx++
				ch = text[idx]
			}
		}

		start := idx

		plainContent := true

		if DoStrict && ch == '<' {
			// check to see if an HTML or MathML element is at the beginning of a content string
			if HTMLAhead(text, idx, txtlen) != 0 {
				plainContent = false
			}
		}

		if plainContent && ch == '<' {

			// at start of element
			idx++
			ch = text[idx]

			// check for legal first character of element
			if InFirst[ch] {

				// read element name
				start = idx
				idx++

				ch = text[idx]
				for InElement[ch] {
					idx++
					ch = text[idx]
				}

				str := text[start:idx]

				if ch == '>' {

					// end of element
					idx++

					return STARTTAG, NONE, str[:], "", idx

				} else if ch == '/' {

					// self-closing element without attributes
					idx++
					ch = text[idx]
					if ch != '>' {
						// skip past unexpected blanks
						for InBlank[ch] {
							idx++
							ch = text[idx]
						}
						if ch != '>' {
							fmt.Fprintf(os.Stderr, "\nSelf-closing element missing right angle bracket\n")
						}
					}
					idx++

					return SELFTAG, NONE, str[:], "", idx

				} else if InBlank[ch] {

					// attributes
					idx++
					ch = text[idx]
					// skip past unexpected blanks
					for InBlank[ch] {
						idx++
						ch = text[idx]
					}
					start = idx
					for ch != '<' && ch != '>' {
						idx++
						ch = text[idx]
					}
					if ch != '>' {
						fmt.Fprintf(os.Stderr, "\nAttributes not followed by right angle bracket\n")
					}
					// walk back past trailing blanks
					lst := idx - 1
					ch = text[lst]
					for InBlank[ch] && lst > start {
						lst--
						ch = text[lst]
					}
					if ch == '/' {
						// self-closing
						atr := text[start:lst]
						idx++

						return SELFTAG, NONE, str[:], atr[:], idx
					}
					atr := text[start:idx]
					idx++

					return STARTTAG, NONE, str[:], atr[:], idx

				} else {

					if CountLines {
						fmt.Fprintf(os.Stderr, "\nUnexpected punctuation '%c' in XML element, line %d\n", ch, currentLineCount(idx))
					} else {
						fmt.Fprintf(os.Stderr, "\nUnexpected punctuation '%c' in XML element\n", ch)
					}

					return STARTTAG, NONE, str[:], "", idx
				}

				// other punctuation character immediately after first angle bracket

			} else if ch == '/' {

				// at start of end tag
				idx++
				start = idx
				ch = text[idx]
				// expect legal first character of element
				if InFirst[ch] {
					idx++
					ch = text[idx]
					for InElement[ch] {
						idx++
						ch = text[idx]
					}
					str := text[start:idx]
					if ch != '>' {
						// skip past unexpected blanks
						for InBlank[ch] {
							idx++
							ch = text[idx]
						}
						if ch != '>' {
							fmt.Fprintf(os.Stderr, "\nUnexpected characters after end element name\n")
						}
					}
					idx++

					return STOPTAG, NONE, str[:], "", idx
				}
				// legal character not found after slash
				if CountLines {
					fmt.Fprintf(os.Stderr, "\nUnexpected punctuation '%c' in XML element, line %d\n", ch, currentLineCount(idx))
				} else {
					fmt.Fprintf(os.Stderr, "\nUnexpected punctuation '%c' in XML element\n", ch)
				}

			} else if ch == '!' {

				// skip !DOCTYPE, !COMMENT, and ![CDATA[
				idx++
				start = idx
				ch = text[idx]
				Which = NOTAG
				SkipTo = ""
				if ch == '[' && strings.HasPrefix(text[idx:], "[CDATA[") {
					Which = CDATATAG
					SkipTo = "]]>"
					start += 7
				} else if ch == '-' && strings.HasPrefix(text[idx:], "--") {
					Which = COMMENTTAG
					SkipTo = "-->"
					start += 2
				} else if ch == 'D' && strings.HasPrefix(text[idx:], "DOCTYPE") {
					Which = DOCTYPETAG
					SkipTo = ">"
				}
				if Which != NOTAG && SkipTo != "" {
					which := Which
					// CDATA or COMMENT block may contain internal angle brackets
					found := strings.Index(text[idx:], SkipTo)
					if found < 0 {
						// string stops in middle of CDATA or COMMENT
						if inp != nil {
							str := text[start:]
							if HasFlankingSpace(str) {
								str = strings.TrimSpace(str)
							}

							if CountLines {
								updateLineCount(txtlen)
							}

							// signal end of current block
							Text = ""

							// leave Which and SkipTo values unchanged as another continuation signal
							// send CDATA or COMMENT contents
							return which, NONE, str[:], "", 0
						}

						return ISCLOSED, NONE, "", "", idx
					}
					// adjust position past end of CDATA or COMMENT
					if inp != nil {
						idx += found
						str := text[start:idx]
						if HasFlankingSpace(str) {
							str = strings.TrimSpace(str)
						}
						idx += len(SkipTo)
						// clear tracking variables
						Which = NOTAG
						SkipTo = ""
						// send CDATA or COMMENT contents
						return which, NONE, str[:], "", idx
					}

					idx += found + len(SkipTo)
					return NOTAG, NONE, "", "", idx
				}
				// otherwise just skip to next right angle bracket
				for ch != '>' {
					idx++
					ch = text[idx]
				}
				idx++
				return NOTAG, NONE, "", "", idx

			} else if ch == '?' {

				// skip ?xml and ?processing instructions
				idx++
				ch = text[idx]
				for ch != '>' {
					idx++
					ch = text[idx]
				}
				idx++
				return NOTAG, NONE, "", "", idx

			} else {

				if CountLines {
					fmt.Fprintf(os.Stderr, "\nUnexpected punctuation '%c' in XML element, line %d\n", ch, currentLineCount(idx))
				} else {
					fmt.Fprintf(os.Stderr, "\nUnexpected punctuation '%c' in XML element\n", ch)
				}
			}

		} else if ch != '>' {

			// at start of contents
			start = idx

			hasMarkup := false
			hasNonASCII := false

			// find end of contents
			if AllowEmbed {

				for {
					for InContent[ch] {
						idx++
						ch = text[idx]
					}
					// set flags to speed up conditional content processing
					if ch == '&' {
						idx++
						ch = text[idx]
						if ch == 'a' {
							if strings.HasPrefix(text[idx:], "amp;") {
								hasMarkup = true
							}
						} else if ch == 'g' {
							if strings.HasPrefix(text[idx:], "gt;") {
								hasMarkup = true
							}
						} else if ch == 'l' {
							if strings.HasPrefix(text[idx:], "lt;") {
								hasMarkup = true
							}
						}
						continue
					}
					if ch > 127 {
						hasNonASCII = true
						idx++
						ch = text[idx]
						continue
					}
					if ch == '<' && DoStrict {
						// optionally allow HTML text formatting elements and super/subscripts
						advance := HTMLAhead(text, idx, txtlen)
						if advance > 0 {
							idx += advance
							if idx < txtlen {
								ch = text[idx]
							}
							plainContent = false
							continue
						}
					}
					break
				}

			} else {
				for ch != '<' && ch != '>' {
					idx++
					ch = text[idx]
				}
			}

			// trim back past trailing blanks
			lst := idx - 1
			ch = text[lst]
			if InBlank[ch] && lst > start {
				ctype |= RGTSPACE
				lst--
				ch = text[lst]
				for InBlank[ch] && lst > start {
					lst--
					ch = text[lst]
				}
			}

			str := text[start : lst+1]

			if AllowEmbed {
				if !plainContent {
					ctype |= MIXED
				}
				if hasMarkup {
					ctype |= AMPER
				}
				if hasNonASCII {
					ctype |= ASCII
				}
			}

			return CONTENTTAG, ctype, str[:], "", idx
		}

		return BADTAG, NONE, "", "", idx
	}

	// node farm variables
	FarmPos := 0
	FarmMax := FarmSize
	FarmItems := make([]Node, FarmMax)

	// allocate multiple nodes in a large array for memory management efficiency
	nextNode := func(strt, attr, prnt string) *Node {

		// if farm array slots used up, allocate new array
		if FarmPos >= FarmMax {
			FarmItems = make([]Node, FarmMax)
			FarmPos = 0
		}

		if FarmItems == nil {
			return nil
		}

		// take node from next available slot in farm array
		node := &FarmItems[FarmPos]

		node.Name = strt[:]
		node.Attributes = attr[:]
		node.Parent = prnt[:]

		FarmPos++

		return node
	}

	// Parse tokens into tree structure for exploration

	// parseSpecial recursive definition
	var parseSpecial func(string, string, string) (*Node, bool)

	// parse XML tags into tree structure for searching, no ContentMods flags set
	parseSpecial = func(strt, attr, prnt string) (*Node, bool) {

		var obj *Node
		ok := true

		// obtain next node from farm
		node := nextNode(strt, attr, prnt)
		if node == nil {
			return nil, false
		}

		var lastNode *Node

		status := START
		for {
			tag, _, name, attr, idx := nextToken(Idx)
			Idx = idx

			if tag == BADTAG {
				if CountLines {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element, line %d\n", Line)
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element\n")
				}
				break
			}
			if tag == ISCLOSED {
				break
			}

			switch tag {
			case STARTTAG:
				if status == CHAR {
					fmt.Fprintf(os.Stderr, "ERROR: UNEXPECTED MIXED CONTENT <%s> in <%s>\n", name, prnt)
				}
				// read sub tree
				obj, ok = parseSpecial(name, attr, node.Name)
				if !ok {
					break
				}

				// adding next child to end of linked list gives better performance than appending to slice of nodes
				if node.Children == nil {
					node.Children = obj
				}
				if lastNode != nil {
					lastNode.Next = obj
				}
				lastNode = obj
				status = STOP
			case STOPTAG:
				// pop out of recursive call
				return node, ok
			case CONTENTTAG:
				node.Contents = name
				status = CHAR
			case SELFTAG:
				if attr == "" {
					// ignore if self-closing tag has no attributes
					continue
				}

				// self-closing tag has no contents, just create child node
				obj = nextNode(name, attr, node.Name)

				if node.Children == nil {
					node.Children = obj
				}
				if lastNode != nil {
					lastNode.Next = obj
				}
				lastNode = obj
				status = OTHER
				// continue on same level
			default:
				status = OTHER
			}
		}

		return node, ok
	}

	// parseLevel recursive definition
	var parseLevel func(string, string, string) (*Node, bool)

	// parse XML tags into tree structure for searching, some ContentMods flags set
	parseLevel = func(strt, attr, prnt string) (*Node, bool) {

		var obj *Node
		ok := true

		// obtain next node from farm
		node := nextNode(strt, attr, prnt)
		if node == nil {
			return nil, false
		}

		var lastNode *Node

		status := START
		for {
			tag, ctype, name, attr, idx := nextToken(Idx)
			Idx = idx

			if CountLines && Idx > 0 {
				updateLineCount(Idx)
			}

			if tag == BADTAG {
				if CountLines {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element, line %d\n", Line)
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element\n")
				}
				break
			}
			if tag == ISCLOSED {
				break
			}

			switch tag {
			case STARTTAG:
				if status == CHAR {
					if DoStrict {
						fmt.Fprintf(os.Stderr, "ERROR: UNRECOGNIZED MIXED CONTENT <%s> in <%s>\n", name, prnt)
					} else if !DoMixed {
						fmt.Fprintf(os.Stderr, "ERROR: UNEXPECTED MIXED CONTENT <%s> in <%s>\n", name, prnt)
					}
				}
				// read sub tree
				obj, ok = parseLevel(name, attr, node.Name)
				if !ok {
					break
				}

				// adding next child to end of linked list gives better performance than appending to slice of nodes
				if node.Children == nil {
					node.Children = obj
				}
				if lastNode != nil {
					lastNode.Next = obj
				}
				lastNode = obj
				status = STOP
			case STOPTAG:
				// pop out of recursive call
				return node, ok
			case CONTENTTAG:
				if DoMixed {
					// create unnamed child node for content string
					con := nextNode("", "", "")
					if con == nil {
						break
					}
					txt := CleanupContents(name, (ctype&ASCII) != 0, (ctype&AMPER) != 0, (ctype&MIXED) != 0)
					if (ctype & LFTSPACE) != 0 {
						txt = " " + txt
					}
					if (ctype & RGTSPACE) != 0 {
						txt += " "
					}
					con.Contents = txt
					if node.Children == nil {
						node.Children = con
					}
					if lastNode != nil {
						lastNode.Next = con
					}
					lastNode = con
				} else {
					node.Contents = CleanupContents(name, (ctype&ASCII) != 0, (ctype&AMPER) != 0, (ctype&MIXED) != 0)
				}
				status = CHAR
			case SELFTAG:
				if attr == "" {
					// ignore if self-closing tag has no attributes
					continue
				}

				// self-closing tag has no contents, just create child node
				obj = nextNode(name, attr, node.Name)

				if node.Children == nil {
					node.Children = obj
				}
				if lastNode != nil {
					lastNode.Next = obj
				}
				lastNode = obj
				status = OTHER
				// continue on same level
			default:
				status = OTHER
			}
		}

		return node, ok
	}

	// parseIndex recursive definition
	var parseIndex func(string, string, string) string

	// parse XML tags looking for trie index element
	parseIndex = func(strt, attr, prnt string) string {

		versn := ""

		// check for version attribute match
		if attr != "" && find.Versn != "" && strings.Contains(attr, find.Versn) {
			if strt == find.Match || find.Match == "" {
				if find.Parent == "" || prnt == find.Parent {
					attribs := ParseAttributes(attr)
					for i := 0; i < len(attribs)-1; i += 2 {
						if attribs[i] == find.Versn {
							versn = attribs[i+1]
						}
					}
				}
			}
		}

		// check for attribute index match
		if attr != "" && find.Attrib != "" && strings.Contains(attr, find.Attrib) {
			if strt == find.Match || find.Match == "" {
				if find.Parent == "" || prnt == find.Parent {
					attribs := ParseAttributes(attr)
					for i := 0; i < len(attribs)-1; i += 2 {
						if attribs[i] == find.Attrib {
							return attribs[i+1]
						}
					}
				}
			}
		}

		for {
			tag, _, name, attr, idx := nextToken(Idx)
			Idx = idx

			if tag == BADTAG {
				if CountLines {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element, line %d\n", Line)
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element\n")
				}
				break
			}
			if tag == ISCLOSED {
				break
			}

			switch tag {
			case STARTTAG:
				id := parseIndex(name, attr, strt)
				if id != "" {
					return id
				}
			case SELFTAG:
			case STOPTAG:
				// break recursion
				return ""
			case CONTENTTAG:
				// check for content index match
				if strt == find.Match || find.Match == "" {
					if find.Parent == "" || prnt == find.Parent {
						// append version if specified as parent/element@attribute^version
						if versn != "" {
							name += "."
							name += versn
						}
						if ids != nil {
							ids(name)
						} else {
							return name
						}
					}
				}
			default:
			}
		}

		return ""
	}

	// ParseXML

	// stream all tokens through callback
	if tokens != nil {

		for {
			tag, ctype, name, attr, idx := nextToken(Idx)
			Idx = idx

			if CountLines && Idx > 0 {
				updateLineCount(Idx)
			}

			if tag == BADTAG {
				if CountLines {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element, line %d\n", Line)
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element\n")
				}
				break
			}

			tkn := Token{tag, ctype, name, attr, idx, Line}

			tokens(tkn)

			if tag == ISCLOSED {
				break
			}
		}

		return nil, ""
	}

	// find value of index element
	if find != nil && find.Index != "" {

		// return indexed identifier

		tag, _, name, attr, idx := nextToken(Idx)

		// loop until start tag
		for {
			Idx = idx

			if tag == BADTAG {
				if CountLines {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element, line %d\n", Line)
				} else {
					fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element\n")
				}
				break
			}
			if tag == ISCLOSED {
				break
			}

			if tag == STARTTAG {
				break
			}

			tag, _, name, attr, idx = nextToken(Idx)
		}

		return nil, parseIndex(name, attr, parent)
	}

	// otherwise create node tree for general data extraction
	tag, _, name, attr, idx := nextToken(Idx)

	// loop until start tag
	for {
		Idx = idx

		if tag == BADTAG {
			if CountLines {
				fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element, line %d\n", Line)
			} else {
				fmt.Fprintf(os.Stderr, "\nERROR: Unparsable XML element\n")
			}
			break
		}
		if tag == ISCLOSED {
			break
		}

		if tag == STARTTAG {
			break
		}

		tag, _, name, attr, idx = nextToken(Idx)
	}

	if ContentMods {
		// slower parser also handles mixed content
		top, ok := parseLevel(name, attr, parent)

		if !ok {
			return nil, ""
		}

		return top, ""
	}

	// fastest parsing with no ContentMods flags
	top, ok := parseSpecial(name, attr, parent)

	if !ok {
		return nil, ""
	}

	return top, ""
}

// specialized public ParseXML shortcuts

func ParseRecord(Text, parent string) *Node {

	pat, _ := ParseXML(Text, parent, nil, nil, nil, nil)

	return pat
}

func FindIdentifier(Text, parent string, find *Find) string {

	_, id := ParseXML(Text, parent, nil, nil, find, nil)

	return id
}

func FindIdentifiers(Text, parent string, find *Find, ids func(string)) {

	ParseXML(Text, parent, nil, nil, find, ids)
}

func StreamValues(Text, parent string, stream func(string, string, string)) {

	elementName := ""
	attributeName := ""

	streamer := func(tkn Token) {

		switch tkn.Tag {
		case STARTTAG:
			elementName = tkn.Name
			attributeName = tkn.Attr
		case CONTENTTAG:
			// send element name and content to callback
			stream(elementName, attributeName, tkn.Name)
		default:
		}
	}

	ParseXML(Text, parent, nil, streamer, nil, nil)
}

func CreateTokenizer(inp <-chan string) <-chan Token {

	if inp == nil {
		return nil
	}

	out := make(chan Token, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create tokenizer channel\n")
		os.Exit(1)
	}

	// xmlTokenizer sends XML tokens through channel
	xmlTokenizer := func(inp <-chan string, out chan<- Token) {

		// close channel when all records have been processed
		defer close(out)

		// parse XML and send tokens through channel
		ParseXML("", "", inp, func(tkn Token) { out <- tkn }, nil, nil)
	}

	// launch single tokenizer goroutine
	go xmlTokenizer(inp, out)

	return out
}

// UNSHUFFLER USES HEAP TO RESTORE OUTPUT OF MULTIPLE CONSUMERS TO ORIGINAL RECORD ORDER

type Extract struct {
	Index int
	Ident string
	Text  string
	Data  []byte
}

type ExtractHeap []Extract

// methods that satisfy heap.Interface
func (h ExtractHeap) Len() int {
	return len(h)
}
func (h ExtractHeap) Less(i, j int) bool {
	return h[i].Index < h[j].Index
}
func (h ExtractHeap) Swap(i, j int) {
	h[i], h[j] = h[j], h[i]
}
func (h *ExtractHeap) Push(x interface{}) {
	*h = append(*h, x.(Extract))
}
func (h *ExtractHeap) Pop() interface{} {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

func CreateProducer(pat, star string, rdr <-chan string) <-chan Extract {

	if rdr == nil {
		return nil
	}

	out := make(chan Extract, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create producer channel\n")
		os.Exit(1)
	}

	// xmlProducer sends partitioned XML strings through channel
	xmlProducer := func(pat, star string, rdr <-chan string, out chan<- Extract) {

		// close channel when all records have been processed
		defer close(out)

		rec := 0

		// partition all input by pattern and send XML substring to available consumer through channel
		PartitionPattern(pat, star, rdr,
			func(str string) {
				rec++
				out <- Extract{rec, "", str, nil}
			})
	}

	// launch single producer goroutine
	go xmlProducer(pat, star, rdr, out)

	return out
}

func CreateUnshuffler(inp <-chan Extract) <-chan Extract {

	if inp == nil {
		return nil
	}

	out := make(chan Extract, ChanDepth)
	if out == nil {
		fmt.Fprintf(os.Stderr, "\nERROR: Unable to create unshuffler channel\n")
		os.Exit(1)
	}

	// xmlUnshuffler restores original order with heap
	xmlUnshuffler := func(inp <-chan Extract, out chan<- Extract) {

		// close channel when all records have been processed
		defer close(out)

		// initialize empty heap
		hp := &ExtractHeap{}
		heap.Init(hp)

		// index of next desired result
		next := 1

		delay := 0

		for ext := range inp {

			// push result onto heap
			heap.Push(hp, ext)

			// read several values before checking to see if next record to print has been processed
			if delay < HeapSize {
				delay++
				continue
			}

			delay = 0

			for hp.Len() > 0 {

				// remove lowest item from heap, use interface type assertion
				curr := heap.Pop(hp).(Extract)

				if curr.Index > next {

					// record should be printed later, push back onto heap
					heap.Push(hp, curr)
					// and go back to waiting on input channel
					break
				}

				// send even if empty to get all record counts for reordering
				out <- Extract{curr.Index, curr.Ident, curr.Text, curr.Data}

				// prevent ambiguous -limit filter from clogging heap (deprecated)
				if curr.Index == next {
					// increment index for next expected match
					next++
				}

				// keep checking heap to see if next result is already available
			}
		}

		// send remainder of heap to output
		for hp.Len() > 0 {
			curr := heap.Pop(hp).(Extract)

			out <- Extract{curr.Index, curr.Ident, curr.Text, curr.Data}
		}
	}

	// launch single unshuffler goroutine
	go xmlUnshuffler(inp, out)

	return out
}

// PrintDuration prints processing rate and program duration
func PrintDuration(name string, recordCount, byteCount int) {

	stopTime := time.Now()
	duration := stopTime.Sub(StartTime)
	seconds := float64(duration.Nanoseconds()) / 1e9

	prec := 3
	if seconds >= 100 {
		prec = 1
	} else if seconds >= 10 {
		prec = 2
	}

	if recordCount >= 1000000 {
		throughput := float64(recordCount/100000) / 10.0
		fmt.Fprintf(os.Stderr, "\nXtract processed %.1f million %s in %.*f seconds", throughput, name, prec, seconds)
	} else {
		fmt.Fprintf(os.Stderr, "\nXtract processed %d %s in %.*f seconds", recordCount, name, prec, seconds)
	}

	if seconds >= 0.001 && recordCount > 0 {
		rate := int(float64(recordCount) / seconds)
		if rate >= 1000000 {
			fmt.Fprintf(os.Stderr, " (%d million %s/second", rate/1000000, name)
		} else {
			fmt.Fprintf(os.Stderr, " (%d %s/second", rate, name)
		}
		if byteCount > 0 {
			rate := int(float64(byteCount) / seconds)
			if rate >= 1000000 {
				fmt.Fprintf(os.Stderr, ", %d megabytes/second", rate/1000000)
			} else if rate >= 1000 {
				fmt.Fprintf(os.Stderr, ", %d kilobytes/second", rate/1000)
			} else {
				fmt.Fprintf(os.Stderr, ", %d bytes/second", rate)
			}
		}
		fmt.Fprintf(os.Stderr, ")")
	}

	fmt.Fprintf(os.Stderr, "\n\n")
}

// CREATE COMMON DRIVER TABLES

// InitTables creates lookup tables to simplify the tokenizer
func InitTables() {

	for i := range InBlank {
		InBlank[i] = false
	}
	InBlank[' '] = true
	InBlank['\t'] = true
	InBlank['\n'] = true
	InBlank['\r'] = true
	InBlank['\f'] = true

	// first character of element cannot be a digit, dash, or period
	for i := range InFirst {
		InFirst[i] = false
	}
	for ch := 'A'; ch <= 'Z'; ch++ {
		InFirst[ch] = true
	}
	for ch := 'a'; ch <= 'z'; ch++ {
		InFirst[ch] = true
	}
	InFirst['_'] = true
	// extend legal initial letter with at sign and digits to handle biological data converted from JSON
	InFirst['@'] = true
	for ch := '0'; ch <= '9'; ch++ {
		InFirst[ch] = true
	}

	// remaining characters also includes colon for namespace
	for i := range InElement {
		InElement[i] = false
	}
	for ch := 'A'; ch <= 'Z'; ch++ {
		InElement[ch] = true
	}
	for ch := 'a'; ch <= 'z'; ch++ {
		InElement[ch] = true
	}
	for ch := '0'; ch <= '9'; ch++ {
		InElement[ch] = true
	}
	InElement['_'] = true
	InElement['-'] = true
	InElement['.'] = true
	InElement[':'] = true

	// embedded markup and math tags are lower case
	for i := range InLower {
		InLower[i] = false
	}
	for ch := 'a'; ch <= 'z'; ch++ {
		InLower[ch] = true
	}
	for ch := '0'; ch <= '9'; ch++ {
		InLower[ch] = true
	}
	InLower['_'] = true
	InLower['-'] = true
	InLower['.'] = true
	InLower[':'] = true

	// shortcut to find <, >, or &, or non-ASCII
	for i := range InContent {
		InContent[i] = false
	}
	for i := 0; i <= 127; i++ {
		InContent[i] = true
	}
	InContent['<'] = false
	InContent['>'] = false
	InContent['&'] = false

	IdxFields = append(IdxFields,
		"CHEM",
		"CODE",
		"CONV",
		"DISZ",
		"GENE",
		"NORM",
		"PATH",
		"PIPE",
		"STEM",
		"THME",
		"TREE",
		"YEAR")
}

// GO AUTOMATIC INITIALIZER

func init() {
	StartTime = time.Now()

	InitTables()
}
