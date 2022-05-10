 
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


########################### URL and paths #########################
our $HOMEPAGE = "http://localhost/panexplorer";
our $WEB_DIR = "http://localhost/panexplorer";
our $HOME_DIR = "/var/www/html/panexplorer/";
our $CGI_DIR = "/var/www/cgi-bin/panexplorer/";
our $CGI_WEB_DIR    = "https://localhost/cgi-bin/panexplorer";
our $TEMP_EXECUTION_DIR = "/var/www/html/panexplorer/tmp";


our $NETWORK_IMAGES_DIR = $HOME_DIR . "/network_images/";

our $R_DIR          = $HOME_DIR . "/R";
our $JAVASCRIPT_DIR = $WEB_DIR . "/javascript";
our $IMAGES_DIR     = $WEB_DIR . "/images";
our $STYLE_DIR      = $WEB_DIR . "/styles";

our $EXAMPLES_DIR = $HOME_DIR . "/examples";

our $DATA_DIR = "$CGI_DIR/data";

our $ADMIN_MAIL = "";

our $BUG_REPORT_PAGE = "";

our $TOOLS_DIR = "$CGI_DIR/tools";
our $DNADIST_EXE ="$TOOLS_DIR/PHYLIP/phylip-3.69/exe/dnadist";
our $READSEQ_EXE = "java -jar $TOOLS_DIR/readseq/readseq.jar";
our $FASTME_EXE = "$TOOLS_DIR/fastme/FastME_2.07/fastme_linux64";
our $MUSCLE_EXE = "$TOOLS_DIR/muscle3.8.31_i86linux64";
our $ROOTING_EXE = "java -jar $TOOLS_DIR/rooting/Rootings_54.jar";
our $HAPLOPHYLE_EXE = "java -jar $TOOLS_DIR/haplophyle/NetworkCreator_fat.jar"; 

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
                   
