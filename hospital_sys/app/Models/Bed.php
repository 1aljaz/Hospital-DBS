<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Bed extends Model
{
    use HasFactory;

    protected $fillable = [
        'room_id',
        'status',
    ];

    public function room()
    {
        return $this->belongsTo(Room::class);
    }

    public function admissions()
    {
        return $this->hasMany(Admission::class);
    }
}
