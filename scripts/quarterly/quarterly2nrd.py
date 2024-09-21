#!/usr/bin/env python3

import sys
import os
import pandas as pd
from argparse import ArgumentParser
from tqdm import tqdm

VERSION = '0.1'
MYNAME = sys.argv[0].replace('./', '')
MYDIR = os.path.abspath(os.path.dirname(__file__))

parser=ArgumentParser(
    description = "Converts a WhoisXML API legacy Quarterly WHOIS Database file to NRD format.",
    prog=MYNAME)

parser.add_argument('infile', type=str, help='Quarterly csv to convert.')

parser.add_argument('outfile', type=str, help='File to store the result in. Should not exist.')

parser.add_argument('reasonfield', type=str, help="This will be in the 'reason' field. Recommended: database version, like 'gtld_v48'.")

parser.add_argument('--version',
                    help='Print version information and exit.',
                    action='version',
                    version=MYNAME + ' ver. ' + VERSION + '\n(c) WhoisXML API, Inc.')

parser.add_argument('--chunksize',
                    type=int,
                    help='Size of chunks of the csv file to be read and processed at once, defaults to 1 0000.',
                    default=10000,
                    required=False)

parser.add_argument('--progress',
                    help="Display progress bar. For experiment only as the bar is on stdout.",
                    action="store_true")

ARGS = parser.parse_args()


if os.path.exists(ARGS.outfile):
    raise ValueError('%s already exists, not overwriting.'%(ARGS.outfile))

NRD_FIELDS = ["reason","domainName","registrarName","registrarIANAID","whoisServer","nameServers","createdDateRaw","updatedDateRaw","expiresDateRaw","createdDateParsed","updatedDateParsed","expiresDateParsed","status","registryDataRawText","whoisRecordRawText","auditUpdatedDate","contactEmail","registrant_rawText","registrant_email","registrant_name","registrant_organization","registrant_street1","registrant_street2","registrant_street3","registrant_street4","registrant_city","registrant_state","registrant_postalCode","registrant_country","registrant_fax","registrant_faxExt","registrant_telephone","registrant_telephoneExt","administrativeContact_rawText","administrativeContact_email","administrativeContact_name","administrativeContact_organization","administrativeContact_street1","administrativeContact_street2","administrativeContact_street3","administrativeContact_street4","administrativeContact_city","administrativeContact_state","administrativeContact_postalCode","administrativeContact_country","administrativeContact_fax","administrativeContact_faxExt","administrativeContact_telephone","administrativeContact_telephoneExt","billingContact_rawText","billingContact_email","billingContact_name","billingContact_organization","billingContact_street1","billingContact_street2","billingContact_street3","billingContact_street4","billingContact_city","billingContact_state","billingContact_postalCode","billingContact_country","billingContact_fax","billingContact_faxExt","billingContact_telephone","billingContact_telephoneExt","technicalContact_rawText","technicalContact_email","technicalContact_name","technicalContact_organization","technicalContact_street1","technicalContact_street2","technicalContact_street3","technicalContact_street4","technicalContact_city","technicalContact_state","technicalContact_postalCode","technicalContact_country","technicalContact_fax","technicalContact_faxExt","technicalContact_telephone","technicalContact_telephoneExt","zoneContact_rawText","zoneContact_email","zoneContact_name","zoneContact_organization","zoneContact_street1","zoneContact_street2","zoneContact_street3","zoneContact_street4","zoneContact_city","zoneContact_state","zoneContact_postalCode","zoneContact_country","zoneContact_fax","zoneContact_faxExt","zoneContact_telephone","zoneContact_telephoneExt"]

RENAME_FIELDS = {'createdDate':'createdDateRaw',
                 'updatedDate':'updatedDateRaw',
                 'expiresDate':'expiresDateRaw',
                 'standardRegCreatedDate':'createdDateParsed',
                 'standardRegUpdatedDate':'updatedDateParsed',
                 'standardRegExpiresDate':'expiresDateParsed',
                 'Audit_auditUpdatedDate':'auditUpdatedDate',
                 'RegistryData_rawText':'registryDataRawText',
                 'WhoisRecord_rawText':'whoisRecordRawText'}

if ARGS.progress:
    iterator = tqdm(pd.read_csv(ARGS.infile,
                                chunksize=ARGS.chunksize,
                                keep_default_na=False),
                    desc='Converting') 
else:
    iterator = pd.read_csv(ARGS.infile,
                           chunksize=ARGS.chunksize,
                           keep_default_na=False)
for chunk in iterator:
        chunk.rename(columns=RENAME_FIELDS, inplace=True)
        chunk['reason'] = ARGS.reasonfield
        newfields = [field for field in NRD_FIELDS if field in set(chunk.keys())]
        chunk = chunk[newfields]
        chunk.to_csv(ARGS.outfile,
                     index=False,
                     mode='a',
                     header=not os.path.exists(ARGS.outfile))
