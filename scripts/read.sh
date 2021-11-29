#!/bin/bash
# Sample script to read NRD 2.0 Ultimate Data Feed File
# 28 Nov 2021 
# ed@whoisxmlapi.com

IFS=','

unknown=0
discovered=0
added=0
dropped=0
updated=0
line=0

while read reason domainName registrarName registrarIANAID whoisServer nameServers createdDateRaw updatedDateRaw expiresDateRaw createdDateParsed updatedDateParsed expiresDateParsed status registryDataRawText whoisRecordRawText auditUpdatedDate contactEmail registrant_rawText registrant_email registrant_name registrant_organization registrant_street1 registrant_street2 registrant_street3 registrant_street4 registrant_city registrant_state registrant_postalCode registrant_country registrant_fax registrant_faxExt registrant_telephone registrant_telephoneExt administrativeContact_rawText administrativeContact_email administrativeContact_name administrativeContact_organization administrativeContact_street1 administrativeContact_street2 administrativeContact_street3 administrativeContact_street4 administrativeContact_city administrativeContact_state administrativeContact_postalCode administrativeContact_country administrativeContact_fax administrativeContact_faxExt administrativeContact_telephone administrativeContact_telephoneExt billingContact_rawText billingContact_email billingContact_name billingContact_organization billingContact_street1 billingContact_street2 billingContact_street3 billingContact_street4 billingContact_city billingContact_state billingContact_postalCode billingContact_country billingContact_fax billingContact_faxExt billingContact_telephone billingContact_telephoneExt technicalContact_rawText technicalContact_email technicalContact_name technicalContact_organization technicalContact_street1 technicalContact_street2 technicalContact_street3 technicalContact_street4 technicalContact_city technicalContact_state technicalContact_postalCode technicalContact_country technicalContact_fax technicalContact_faxExt technicalContact_telephone technicalContact_telephoneExt zoneContact_rawText zoneContact_email zoneContact_name zoneContact_organization zoneContact_street1 zoneContact_street2 zoneContact_street3 zoneContact_street4 zoneContact_city zoneContact_state zoneContact_postalCode zoneContact_country zoneContact_fax zoneContact_faxExt zoneContact_telephone zoneContact_telephoneExt
do
   ((line++))
# skip first line in file
   if [[ $line -eq 1 ]]; then
      continue;
   fi

case $reason in

   added)
      ((added++))
      echo "Added....... $domainName, $registrarName, $line"
      ;;
    
   updated)
      ((updated++))
      echo "Updated..... $domainName"
      ;;

   dropped)
      ((dropped++))
      echo "Deleted..... $domainName"
      ;;

   discovered)
      ((discovered++))
      echo "Discovered.. $domainName, $registrarName"
      ;;

   *)
      ((unknown++)) ;;
esac

done < u.csv

echo "Added     : $added"
echo "Dropped   : $dropped"
echo "Updated   : $updated"
echo "Discovered: $discovered"
echo "Unkown    : $unknown"
echo "Done"
