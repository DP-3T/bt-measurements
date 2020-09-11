# README

17x16 = 272 json files

Missing:

07-check14.json.gz
17-check13.json.gz

Backend JSON format

    experiment = [
        [ dateMillisSinceEpoch, reportType, scanInstances ],
        [ dateMillisSinceEpoch, reportType, scanInstances ],
        ...
    ]

    scanInstances = [
        [minAttenuationDb, secondsSinceLastScan, typicalAttenutationDb],
        [minAttenuationDb, secondsSinceLastScan, typicalAttenutationDb],
    ]

