=pod 
=head1 NAME
=head1 SYNOPSIS
=head1 DESCRIPTION  
=head1 LICENSE
    Copyright [1999-2015] Wellcome Trust Sanger Institute and the EMBL-European Bioinformatics Institute
    Copyright [2016-2024] EMBL-European Bioinformatics Institute
    Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
         http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software distributed under the License
    is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and limitations under the License.
=head1 CONTACT
    Please subscribe to the Hive mailing list:  http://listserver.ebi.ac.uk/mailman/listinfo/ehive-users  to discuss Hive-related questions or to be notified of our updates
=cut


package Bio::EnsEMBL::Production::Pipeline::PipeConfig::TestEvent_conf;

use strict;
use warnings;
use Data::Dumper;
use base ('Bio::EnsEMBL::Hive::PipeConfig::HiveGeneric_conf'); # All Hive databases configuration files should inherit from HiveGeneric, directly or indirectly

use strict;
use Bio::EnsEMBL::Hive::PipeConfig::HiveGeneric_conf;
use base ('Bio::EnsEMBL::Production::Pipeline::PipeConfig::Base_conf');
use Bio::EnsEMBL::ApiVersion qw/software_version/;

use Data::Dumper;

sub default_options {
    my $self = shift;
    return {
        %{$self->SUPER::default_options()},
        testdb => 'testdb',
        tgt_uri => 'mysql://root:root@ensmysql:3306/',
        };
}

sub pipeline_wide_parameters {
    my $self = shift;
    return { %{$self->SUPER::pipeline_wide_parameters()},
        testdb    => $self->o('testdb'),
        tgt_uri => 'mysql://root:root@ensmysql:3306/',
    };
}

sub pipeline_analyses {
    my ($self) = @_;
    return [
        {
            -logic_name        => 'TestDummy',
            -module            => 'Bio::EnsEMBL::Hive::RunnableDB::Dummy',
            -flow_into         => 'Test1',
            -input_ids         => [ {} ],
        },
        {
            -logic_name        => 'Test1',
            -module            => 'Bio::EnsEMBL::Hive::RunnableDB::SystemCmd',
            -max_retry_count   => 1,
            -flow_into         => 'Test2',
            -parameters        => {

                                    cmd => 'echo -n eventapp testing',
                                    },
        },
        {
            -logic_name        => 'Test2',
            -module            => 'Bio::EnsEMBL::Hive::RunnableDB::SqlCmd',
            -analysis_capacity => 10,
            -batch_size        => 10,
            -max_retry_count   => 1,
            -parameters        => {
                                    db_conn => $self->o('tgt_uri'),
                                    testdb => $self->o('testdb'),
                                    sql     => 'create database #testdb#',
                                    },
        },

    ];
}

1;
