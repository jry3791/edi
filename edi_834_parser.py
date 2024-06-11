import re
import pandas as pd
import streamlit as st
from io import StringIO

# Function to parse the EDI 834 file
def parse_edi_834(file_content):
    # Regular expression patterns for segments
    pattern_INS = r'INS\*[^~]+'
    pattern_REF = r'REF\*[^~]+'
    pattern_DTP = r'DTP\*[^~]+'
    pattern_NM1 = r'NM1\*[^~]+'
    pattern_N3 = r'N3\*[^~]+'
    pattern_N4 = r'N4\*[^~]+'
    pattern_DMG = r'DMG\*[^~]+'
    pattern_HD = r'HD\*[^~]+'

    # Extract segments
    INS_segments = re.findall(pattern_INS, file_content)
    REF_segments = re.findall(pattern_REF, file_content)
    DTP_segments = re.findall(pattern_DTP, file_content)
    NM1_segments = re.findall(pattern_NM1, file_content)
    N3_segments = re.findall(pattern_N3, file_content)
    N4_segments = re.findall(pattern_N4, file_content)
    DMG_segments = re.findall(pattern_DMG, file_content)
    HD_segments = re.findall(pattern_HD, file_content)

    # Initialize a list to hold records
    records = []

    # Parse each person's data
    for i in range(len(NM1_segments)):
        record = {}
        
        # Parse NM1 segment
        nm1_parts = NM1_segments[i].split('*')
        if len(nm1_parts) >= 10:
            record['Member Name'] = nm1_parts[3] + ' ' + nm1_parts[4]
            record['Member ID'] = nm1_parts[9]
        else:
            continue  # Skip if the segment is incomplete

        # Parse N3 and N4 segments for address
        if i < len(N3_segments):
            n3_parts = N3_segments[i].split('*')
            record['Address'] = n3_parts[1] if len(n3_parts) > 1 else ''
        if i < len(N4_segments):
            n4_parts = N4_segments[i].split('*')
            record['City'] = n4_parts[1] if len(n4_parts) > 1 else ''
            record['State'] = n4_parts[2] if len(n4_parts) > 2 else ''
            record['ZIP'] = n4_parts[3] if len(n4_parts) > 3 else ''

        # Parse DMG segment for demographic information
        if i < len(DMG_segments):
            dmg_parts = DMG_segments[i].split('*')
            record['DOB'] = dmg_parts[2] if len(dmg_parts) > 2 else ''
            record['Gender'] = 'Male' if len(dmg_parts) > 3 and dmg_parts[3] == 'M' else 'Female'

        # Parse REF segment for group ID
        record['Group ID'] = ''
        for ref in REF_segments:
            if ref.startswith(f"REF*1L*{record['Member ID']}"):
                ref_parts = ref.split('*')
                if len(ref_parts) > 2:
                    record['Group ID'] = ref_parts[2]
                break

        # Parse DTP segment for coverage date
        record['Coverage Start Date'] = ''
        for dtp in DTP_segments:
            if 'DTP*348*D8' in dtp:
                dtp_parts = dtp.split('*')
                record['Coverage Start Date'] = dtp_parts[3] if len(dtp_parts) > 3 else ''
                break

        # Append the record to the list
        records.append(record)

    # Convert records to a DataFrame
    df = pd.DataFrame(records)
    return df

# Streamlit UI
st.title("EDI 834 Parser")

uploaded_file = st.file_uploader("Choose an EDI 834 file", type="TXT")

if uploaded_file is not None:
    # Read the file
    file_content = uploaded_file.read().decode("utf-8")

    # Parse the file
    parsed_data = parse_edi_834(file_content)

    # Display the data
    st.write("Parsed EDI 834 Data:")
    st.dataframe(parsed_data)

    # Download the parsed data
    csv = parsed_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download parsed data as CSV",
        data=csv,
        file_name='parsed_edi_834.csv',
        mime='text/csv',
    )
