#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_RECORDS 100
#define MAX_NAME 50
#define MAX_PROGRAMME 50

typedef struct {
    int id;
    char name[MAX_NAME];
    char programme[MAX_PROGRAMME];
    float mark;
} Student;

Student records[MAX_RECORDS];
int record_count = 0;
char database_filename[100];

// Function to open database and load records
void open_database(char* filename) {
    FILE* file = fopen(filename, "r");

    if (file == NULL) {
        printf("CMS: Error - Cannot open database file \"%s\".\n", filename);
        return;
    }

    char line[256];
    record_count = 0;

    // Skip the first 5 lines (header)
    for (int i = 0; i < 5; i++) {
        if (fgets(line, sizeof(line), file) == NULL) break;
    }

    while (fgets(line, sizeof(line), file) != NULL) {
        if (strlen(line) <= 1) continue;

        // Use sscanf to correctly parse tab-separated values
        if (sscanf(line, "%d\t%49[^\t]\t%49[^\t]\t%f",
            &records[record_count].id,
            records[record_count].name,
            records[record_count].programme,
            &records[record_count].mark) == 4) {

            record_count++;
            if (record_count >= MAX_RECORDS) {
                printf("CMS: Warning - Maximum record limit reached.\n");
                break;
            }
        }
    }

    fclose(file);
    strcpy(database_filename, filename);
    printf("CMS: The database file \"%s\" is successfully opened.\n", filename);
}

// Comparator functions for sorting
int compare_id_asc(const void* a, const void* b) {
    return ((Student*)a)->id - ((Student*)b)->id;
}

int compare_id_desc(const void* a, const void* b) {
    return ((Student*)b)->id - ((Student*)a)->id;
}

int compare_mark_asc(const void* a, const void* b) {
    if (((Student*)a)->mark < ((Student*)b)->mark) return -1;
    if (((Student*)a)->mark > ((Student*)b)->mark) return 1;
    return 0;
}

int compare_mark_desc(const void* a, const void* b) {
    if (((Student*)a)->mark > ((Student*)b)->mark) return -1;
    if (((Student*)a)->mark < ((Student*)b)->mark) return 1;
    return 0;
}

// Display records with optional sorting
void show_all_sorted(char* field, char* order) {
    if (record_count == 0) {
        printf("CMS: No records found in the database.\n");
        return;
    }

    // Sorting
    if (strcmp(field, "ID") == 0) {
        if (strcmp(order, "ASC") == 0) qsort(records, record_count, sizeof(Student), compare_id_asc);
        else qsort(records, record_count, sizeof(Student), compare_id_desc);
    }
    else if (strcmp(field, "MARK") == 0) {
        if (strcmp(order, "ASC") == 0) qsort(records, record_count, sizeof(Student), compare_mark_asc);
        else qsort(records, record_count, sizeof(Student), compare_mark_desc);
    }
    else {
        printf("CMS: Invalid sort field.\n");
        return;
    }

    // Display
    printf("CMS: Here are all the records found in the table \"StudentRecords\".\n");
    printf("%-10s %-20s %-30s %-10s\n", "ID", "Name", "Programme", "Mark");
    for (int i = 0; i < record_count; i++) {
        printf("%-10d %-20s %-30s %-10.1f\n",
            records[i].id,
            records[i].name,
            records[i].programme,
            records[i].mark);
    }
}

int main() {
    char command[256];
    char team_name[50] = "P1_1";

    printf("Declaration\n");
    printf("SIT's policy on copying...\n\n");

    printf("Welcome to Class Management System (CMS)\n");
    printf("Type 'HELP' for available commands\n\n");

    while (1) {
        printf("%s: ", team_name);
        fgets(command, sizeof(command), stdin);
        command[strcspn(command, "\n")] = 0;

        if (strcmp(command, "OPEN") == 0) {
            char filename[100];
            sprintf(filename, "%s-CMS.txt", team_name);
            open_database(filename);
        }
        else if (strncmp(command, "SHOW ALL SORT BY", 16) == 0) {
            char field[10], order[5];
            if (sscanf(command + 16, "%s %s", field, order) == 2) {
                show_all_sorted(field, order);
            }
            else {
                printf("CMS: Invalid SORT command format. Use SHOW ALL SORT BY <ID/MARK> <ASC/DESC>\n");
            }
        }
        else if (strcmp(command, "SHOW ALL") == 0) {
            show_all_sorted("ID", "ASC");  // Default sort by ID ascending
        }
        else if (strcmp(command, "EXIT") == 0) {
            printf("CMS: Exiting program. Goodbye!\n");
            break;
        }
        else {
            printf("CMS: Unknown command. Type 'HELP' for available commands.\n");
        }
    }
    return 0;
}