db.createCollection("Batches",
    {
        capped: Boolean(),
        autoIndexId: Boolean(),
        name: String(),
        created_at: ISODate(),
        updated_at: ISODate(),
        files: [],
    }
);
