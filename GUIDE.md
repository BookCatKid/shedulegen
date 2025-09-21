
# Schedule Generator Guide

## Getting Started

There are three ways to use the Schedule Generator:

- **Manual Entry:** Input all of your classes, rooms, and teachers yourself.
- **Import from Google Calendar:** Sign in with your Google account to automatically import your schedule from your calendar.
- **Automatic Extraction:** Use the bookmarklet to extract schedule data from [`ljcds.myschoolapp.com`](https://ljcds.myschoolapp.com).

## Manual Entry

1. Navigate to the main page in your web browser.
2. Enter a title for your schedule (e.g., "My 9th Grade Timetable").
3. Enter all of the information. You do not have to fill in every field.
4. Click the **Generate Schedule** button to create your schedule.

## Import from Google Calendar

The easiest way to import your schedule is directly from your Google Calendar:

1. Click the **"Import from Google Calendar"** button on the main page.
2. Sign in with your Google account when prompted.
3. Grant permission for the app to read your calendar (read-only access).
4. Your schedule will be automatically imported and the form will be populated with your classes and rooms.
5. Review and edit your schedule as needed, then click **Generate Schedule**.

*Note: Teacher information is not available from Google Calendar events, so you'll need to manually enter teacher names if desired.*

## Automatic Extraction

1. **Add the bookmarklet:** Drag the link below to your bookmarks bar, or right-click and create a new bookmark with the following URL:

[Extract Schedule Data][1]
[1]:javascript:(function()%7Bfetch('https%3A%2F%2Fljcds.myschoolapp.com%2Fpodium%2Fdefault.aspx%3Ft%3D52411%26wapp%3D1%26ch%3D1%26svcid%3Dedu'%2C%20%7B%0A%20%20method%3A%20'GET'%2C%0A%20%20credentials%3A%20'include'%0A%7D)%0A.then(response%20%3D%3E%20response.text())%0A.then(html%20%3D%3E%20%7B%0A%20%20const%20parser%20%3D%20new%20DOMParser()%3B%0A%20%20const%20doc%20%3D%20parser.parseFromString(html%2C%20'text%2Fhtml')%3B%0A%0A%20%20const%20divs%20%3D%20doc.querySelectorAll('tr%20td%20div.dir2ItemUserInfoWrap%2C%20tr%20td%20div.dir2ItemUserInfoWrapAlt')%3B%0A%20%20const%20results%20%3D%20%7B%7D%3B%0A%0A%20%20divs.forEach(div%20%3D%3E%20%7B%0A%20%20%20%20const%20nameElem%20%3D%20div.querySelector('div%20%3E%20span')%3B%0A%20%20%20%20const%20roomDiv%20%3D%20Array.from(div.querySelectorAll('div')).find(d%20%3D%3E%20d.innerText.includes('Room%3A'))%3B%0A%20%20%20%20const%20teacherDiv%20%3D%20Array.from(div.querySelectorAll('div')).find(d%20%3D%3E%20d.innerText.includes('Teacher%3A'))%3B%0A%20%20%20%20const%20blockDiv%20%3D%20Array.from(div.querySelectorAll('div')).find(d%20%3D%3E%20d.innerText.includes('Block%3A'))%3B%0A%0A%20%20%20%20let%20className%20%3D%20nameElem%20%3F%20nameElem.textContent.trim()%20%3A%20''%3B%0A%0A%20%20%20%20%2F%2F%20Remove%20unnecessary%20text%20from%20class%20name%0A%20%20%20%20const%20dashNumIndex%20%3D%20className.search(%2F%20-%20%5Cd%2F)%3B%0A%20%20%20%20if%20(dashNumIndex%20!%3D%3D%20-1)%20%7B%0A%20%20%20%20%20%20className%20%3D%20className.slice(0%2C%20dashNumIndex).trim()%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20const%20roomText%20%3D%20roomDiv%20%3F%20roomDiv.textContent.replace('Room%3A'%2C%20'').trim()%20%3A%20''%3B%0A%20%20%20%20const%20teacherText%20%3D%20teacherDiv%20%3F%20teacherDiv.textContent.replace('Teacher%3A'%2C%20'').trim()%20%3A%20''%3B%0A%20%20%20%20const%20blockTextRaw%20%3D%20blockDiv%20%3F%20blockDiv.textContent.replace('Block%3A'%2C%20'').trim()%20%3A%20''%3B%0A%0A%20%20%20%20if%20(blockTextRaw%20%26%26%20!isNaN(Number(blockTextRaw)))%20%7B%0A%20%20%20%20%20%20const%20block%20%3D%20blockTextRaw%3B%0A%0A%20%20%20%20%20%20if%20(!results%5Bblock%5D)%20%7B%0A%20%20%20%20%20%20%20%20results%5Bblock%5D%20%3D%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%3A%20%5B%5D%2C%0A%20%20%20%20%20%20%20%20%20%20room%3A%20%5B%5D%2C%0A%20%20%20%20%20%20%20%20%20%20teacher%3A%20%5B%5D%0A%20%20%20%20%20%20%20%20%7D%3B%0A%20%20%20%20%20%20%7D%0A%0A%20%20%20%20%20%20results%5Bblock%5D.name.push(className)%3B%0A%20%20%20%20%20%20results%5Bblock%5D.room.push(roomText)%3B%0A%20%20%20%20%20%20results%5Bblock%5D.teacher.push(teacherText)%3B%0A%20%20%20%20%7D%0A%20%20%7D)%3B%0A%0A%20%20const%20output%20%3D%20JSON.stringify(results%2C%20null%2C%202)%3B%0A%0A%20%20navigator.clipboard.writeText(output)%0A%20%20%20%20.then(()%20%3D%3E%20alert('Class%20info%20copied%20to%20clipboard%3A%5Cn%5Cn'%20%2B%20output))%0A%20%20%20%20.catch(()%20%3D%3E%20alert('Failed%20to%20copy%20to%20clipboard.%20Here%20is%20the%20data%3A%5Cn%5Cn'%20%2B%20output))%3B%0A%0A%20%20console.log('Extracted%20Class%20Info%3A'%2C%20results)%3B%0A%7D)%0A.catch(err%20%3D%3E%20%7B%0A%20%20console.error('Failed%20to%20fetch%20or%20parse%20HTML%3A'%2C%20err)%3B%0A%20%20alert('Failed%20to%20fetch%20or%20parse%20HTML.%20See%20console%20for%20details.')%3B%0A%7D)%3B%7D)()%3B

2. **Go to [`ljcds.myschoolapp.com`](https://ljcds.myschoolapp.com):** Make sure you are logged in. You can be on any page in the website.
3. **Click the bookmarklet:** The data will be copied to your clipboard. If you have issues, reload the page to make sure that you are logged in, or refer to the troubleshooting section.
4. **Import the data:** Go back to the schedule generator, click the **"Import Classes"** button, paste your JSON data in the text area, and click **"Apply"** to populate all fields automatically. Paste the JSON as-is, without modification.
5. **Generate your schedule:** Click **Generate Schedule** as usual.

## Additional Info


### Permalinks & Sharing

Whenever you edit your schedule, the web address (URL) in your browser will automatically update to include your schedule data. This means:

- **You can bookmark or copy the URL from your browser's address bar** to save or share your exact schedule.
- **Anyone who visits your link** will see your schedule automatically loaded into the form.
- There is no need for a separate "Share" or "Copy Link" button—just use the address bar.
- The link will look like: `https://.../?data=...`


### Saving/Printing

- The schedule is created using a format called `.svg`. To print the schedule, you should be able to directly print the document from your web browser. You can also save it as a PDF from the print dialog.

### Multiple Classes Per Period

When you have multiple classes for one period (like Foundations vs Study Period), the system will:

1. **Prioritize "Foundations"**: If any class name contains "Foundations", it becomes the main class.
2. **Show alternatives**: Other classes appear in gray "also" notes below the input.

**Example:** For period 5 with Foundations and Study Period:

- **Main display**: "Foundations" in "VASC 20" with "Mr. Johnson"
- **Also note**: "also classes: Study Period; rooms: USQuad 102; teachers: Ms. Davis"

### Custom Editing

The schedule is generated as an SVG image, which can be edited in vector graphic software like Adobe Illustrator or Inkscape (or manually!). This allows you to customize colors, fonts, and layout further if desired.

### JSON Format

The schedule generator accepts JSON data in this format:

```json
{
   "1":{
      "name":["Class"],
      "room":["USQuad 999"],
      "teacher":["Ms. Smith"]
   },
   "2":{
      "name":["Foundations", "Study Period"],
      "room":["", "Library"],
      "teacher":["", "Mr. Jones"]
   },
   ...
}
```

### JSON Field Explanations

- **`Keys (1 to 8)`**: Represent periods 1 through 8
- **`name`**: Array of class names. First item is the main class, others appear in "also" notes
- **`room`**: Array of room locations corresponding to each class
- **`teacher`**: Array of teacher names corresponding to each class

### Schedule Output

The generator creates a schedule with:

- **X-Day column** (left): All 8 periods in shorter blocks
- **Times column**: Shows period times and breaks
- **Day 1-4 columns**: Regular day schedules with 4 periods each
      - Day 1: Periods 1, 3, 5, 7
      - Day 2: Periods 2, 4, 6, 8
      - Day 3: Periods 3, 1, 7, 5
      - Day 4: Periods 4, 2, 8, 6

### Free Period Name & Foundations Replacement

- In the schedule form, you can set a **Free Period Name** (default: "Study Period").
- On the X-Day column of your schedule, **any class containing "Foundations" will be replaced with your chosen Free Period Name**.
- This is because there is no foundations course on X-Days.
- If you leave the Free Period Name blank, "Foundations" will remain as-is.

## Troubleshooting

If you encounter issues:

1. **Google Calendar Import Issues:**
   - Make sure you're signed in to the correct Google account
   - Check that your calendar events follow the correct format: "Class Name - Block #"
   - Ensure your calendar has events for the upcoming Monday
   - Try refreshing the page and importing again

2. **General Issues:**
   - Check the browser console for error messages (press F12 or right-click and select "Inspect").
   - Verify your JSON format using a [JSON validator](https://jsonlint.com/) if using manual import.
   - Make sure that you have no more than 2 empty classes/periods.
   - Try refreshing the page and starting over.

3. **Bookmarklet Issues:**
   - Ensure you are on the correct page and logged in to ljcds.myschoolapp.com
   - Try disabling browser extensions that may block scripts or switch to a different browser.
   - If you see "Failed to copy to clipboard", manually copy the JSON from the browser console.

4. **If all else fails, [contact me](mailto:sroff2029@ljcds.org) for assistance.**

##

*Happy scheduling! 📅*
