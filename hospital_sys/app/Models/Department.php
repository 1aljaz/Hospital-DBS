<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Department extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'location',
    ];

    // Relationships
    public function staff()
    {
        return $this->hasMany(Staff::class);
    }

    public function rooms()
    {
        return $this->hasMany(Room::class);
    }
}
