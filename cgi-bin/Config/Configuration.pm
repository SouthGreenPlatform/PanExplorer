 
# Copyright 2019 Alexis Dereeper
#
# ###########################
# # Panexplorer scripts
# ###########################
#
#    This file is part of Panexplorer.
#
#    Panexplorer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Panexplorer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Panexplorer.  If not, see <http://www.gnu.org/licenses/>.

 

=head1 NAME

Config::Configuration - Store all the constants (file and directory names...)

=head1 SYNOPSIS

my $WEB_DIR = $Configuration::WEB_DIR;

=head1 REQUIRES

=head1 DESCRIPTION

This package enable to store all constants which can be used by any program or module : file and directory names...

=cut

package Configuration;

# Package constants
####################

=pod

=head1 CONSTANTS

B<HOMEPAGE>:  String, public

                   URL of the web page

B<WEB_DIR>:  String, public

                   used to define the URL of the web server

B<HOME_DIR>:  String, public

                   used to define the directory of the web server
=cut

########################### URL #########################
our $HOMEPAGE = "https://panexplorer.southgreen.fr/";
our $WEB_DIR = "https://panexplorer.southgreen.fr";


######################## directories ####################
# Absolute path of html public directory, $HOME_DIR must be HTML_DIR (htdocs or public_html folder)
our $HOME_DIR = "/opt/projects/panexplorer.southgreen.fr/prod/htdocs";
# Absolute path of cgi directory
our $CGI_DIR = "/opt/projects/panexplorer.southgreen.fr/prod/cgi-bin";

#All analysis are pocessed in this folder (need to make a specific cron job to remove analysis files periodically)
our $TEMP_EXECUTION_DIR = "/opt/projects/panexplorer.southgreen.fr/tmp";

our $NETWORK_IMAGES_DIR = $HOME_DIR . "/network_images/";

our $R_DIR          = $HOME_DIR . "/R";
our $JAVASCRIPT_DIR = $WEB_DIR . "/javascript";
our $IMAGES_DIR     = $WEB_DIR . "/images";
our $STYLE_DIR      = $WEB_DIR . "/styles";
our $CGI_WEB_DIR    = "https://panexplorer.southgreen.fr/cgi-bin";

our $EXAMPLES_DIR = $HOME_DIR . "/examples";

our $DATA_DIR = "/opt/projects/panexplorer.southgreen.fr/data";

our $ADMIN_MAIL = "";

our $BUG_REPORT_PAGE = "";

our $TOOLS_DIR = "/www/panexplorer.southgreen.fr/tools";
our $DNADIST_EXE ="/opt/projects/sniplay.southgreen.fr/tools/PHYLIP/phylip-3.69/exe/dnadist";
our $READSEQ_EXE = "/opt/java/bin/java -jar /opt/projects/sniplay.southgreen.fr/tools/readseq/readseq.jar";
our $FASTME_EXE = "/opt/projects/sniplay.southgreen.fr/tools/fastme/FastME_2.07/fastme_linux64";
our $MUSCLE_EXE = "/www/panexplorer.southgreen.fr/tools/muscle3.8.31_i86linux64";
our $ROOTING_EXE = "/opt/java/bin/java -jar /www/panexplorer.southgreen.fr/tools/rooting/Rootings_54.jar";

our %COLORS = (
	"Ehrlichia" => "red",
	"Wolbachia" => "green",
	"Anaplasma" => "blue",
	"Neorickettsia" => "purple"
);

=pod

=head1 AUTHORS

Alexis DEREEPER (CIRAD), alexis.dereeper@cirad.fr

=head1 VERSION

Version 0.1

=head1 SEE ALSO

=cut

return 1; # package return
                   
