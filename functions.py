import pandas as pd

def prepp_df_dict(_dict, org_header):
    checks_out = True
    res = {}
    header = []
    for key, value in _dict.items():
        res[value] = []
        header.append(key)
        if not key in org_header:
            print(f'{key} not checking out')
            checks_out = False
    return res, header, checks_out


def get_sheet_values_service(service, ID, _range):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=ID, range=_range).execute()
    return result.get('values', [])


def get_sheet_as_df(service, ID, _range, col_map):
    """
    Hämtar ett sheet från Drive med id ID inom range _range och med
    header mapping enlig col_map.
    
    Returnerar DataFrame
    """

    values = get_sheet_values_service(service, ID, _range)
    # Den faktiska headern i sheeten
    org_header = values[0]

    if not values:
        print('No data found in ' + ID + ', range ' +
              _range + ' with col_map ' + col_map)
    else:
        errors = []

        # Preparerar data:
        # _dict (dict) får keys utefter col_map med tom lista som value för varje key.
        # header (list) sätts utefter col_map (vilka rubriker som skall extraheras)
        # checks_out (boolean) True om col_map keys finns med i org_header annars False
        _dict, header, checks_out = prepp_df_dict(col_map, org_header)

        if checks_out:
            for i, row in enumerate(values):
                if i == 0:
                    # Skippar rubrikraden
                    pass
                else:
                    try:
                        for key in header:
                            # print(f'len(row): {len(row)}')
                            # print(f'org_header.index(key): {org_header.index(key)}')
                            if len(row) <= org_header.index(key):
                                """
                                Raden som plocks ut (row) blir inte alltid lika lång som rubrikraden utan klipps av till kortare längd om celler mot
                                slutet av raden är tomma. Detta gör att man måste kolla om raden är kortare än headerraden för denna rubriken (key)
                                och om så är fallet appenda tom cell (''). Detta för att undvika index out of range error.
                                """
                                _dict[col_map[key]].append('')
                            else:
                                _dict[col_map[key]].append(
                                    row[org_header.index(key)].strip())

                    except Exception as e:
                        errors.append(row)

        else:
            print(f'{col_map} and {org_header} doesn\'t match')
            exit()

    return pd.DataFrame.from_dict(_dict), errors
